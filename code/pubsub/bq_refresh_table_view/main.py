import base64
import json
from google.cloud import bigquery
import logging


def get_table_latest_version_data(bigquery_client, dataset_id, table_id):
    dataset_ref = bigquery_client.dataset(dataset_id)
    dataset = bigquery_client.get_dataset(dataset_ref.dataset_id)

    query = ('SELECT '
             '  table_name, '
             '  max(version) as last_version, '
             '  version_schema '
             'FROM `{}.{}.schema_management` '
             'where table_name = @param_table_name '
             'group by table_name, version_schema '
             'order by max(version) desc limit 1'.format(dataset.project, dataset_id))
    timeout = 30  # in seconds
    param_table_name = bigquery.ScalarQueryParameter('param_table_name', 'STRING', table_id)
    job_config = bigquery.QueryJobConfig()
    job_config.query_parameters = [param_table_name]

    query_job = bigquery_client.query(query, job_config=job_config)  # API request - starts the query

    # Waits for the query to finish
    iterator = query_job.result(timeout=timeout)
    rows = list(iterator)
    return rows[0] if len(rows) > 0 else None


def delete_view(bigquery_client, project_id, dataset_id, table_id):
    try:
        table_view = bigquery_client.get_table('{}.{}.{}_view'.format(project_id, dataset_id, table_id))
        logging.info('Deleting view : `{}`'.format(table_view.table_id))
        bigquery_client.delete_table(table_view)
    except Exception as e:
        pass


def create_view(bigquery_client, project_id,  dataset_id, table_id):
    dataset_ref = bigquery_client.dataset(dataset_id)
    dataset = bigquery_client.get_dataset(dataset_ref.dataset_id)

    view_ref = dataset.table('{}_view'.format(table_id))
    view = bigquery.Table(view_ref)

    table_row_data = get_table_latest_version_data(bigquery_client, dataset_id, table_id)

    if table_row_data is not None:  # table already exists
        table_version = table_row_data.last_version

    # sql_template = "SELECT *, Date(_PARTITIONTIME) as Partition_Date FROM `{}.{}.{}_v{}`".format(project_id, dataset_id, table_id, table_version)
    sql_template = '''
        with last_entity as 
        (
          SELECT 
            Row_number() over (partition by id order by etl_date_updated desc) as rn,
            Date(_PARTITIONTIME) as PartititonDate,
            *  
          FROM `{}.{}.{}_v{}`
        )
        SELECT * FROM last_entity where rn = 1 
    '''.format(project_id, dataset_id, table_id, table_version)

    view.view_query = sql_template.format(project_id, dataset_id, table_id)
    view = bigquery_client.create_table(view)  # API request

    logging.info("Successfully created view at {}".format(view.full_table_id))


def main(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
        Args:
             event (dict): Event payload.
             context (google.cloud.functions.Context): Metadata for the event.
        This function receives in event['data']:
        {
          'project'         : 'project_name',
          'dest_dataset'    : 'dest_dataset',
          'table'           : 'table_name',
          'etl_region'      : 'etl_region'
        }
    """
    logging.getLogger().setLevel(logging.INFO)
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    logging.info('Received message: {}'.format(pubsub_message))
    message = json.loads(pubsub_message)

    project = message['project']
    dataset = message['dest_dataset']
    table = message['table']
    etl_region = message['etl_region']

    bigquery_client = bigquery.Client(project=project)
    delete_view(bigquery_client, project, dataset, table)
    create_view(bigquery_client, project, dataset, table)


# to debug locally
if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    # go to https://www.base64encode.org/
    # encode json object according to project

    # {"project": "taxfyle-qa-data", "dest_dataset": "data_warehouse_us", "table" : "job", "etl_region": "US"}
    # event ={
    #     'data': 'eyJwcm9qZWN0IjogInRheGZ5bGUtcWEtZGF0YSIsICJkZXN0X2RhdGFzZXQiOiAiZGF0YV93YXJlaG91c2VfdXMiLCAidGFibGUiIDogImpvYiIsICJldGxfcmVnaW9uIjogIlVTIn0='
    # }

    # {"project": "taxfyle-qa-data", "dest_dataset": "data_warehouse_us", "table" : "document", "etl_region": "US"}
    event ={
        'data': 'eyJwcm9qZWN0IjogInRheGZ5bGUtcWEtZGF0YSIsICJkZXN0X2RhdGFzZXQiOiAiZGF0YV93YXJlaG91c2VfdXMiLCAidGFibGUiIDogImRvY3VtZW50IiwgImV0bF9yZWdpb24iOiAiVVMifQ=='
    }

    context = {}
    main(event, context)
