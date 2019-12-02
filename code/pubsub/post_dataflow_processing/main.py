import base64
import json
from google.cloud import storage
from google.cloud import bigquery
import logging
import datetime


# -------------------------------------storage functions--------------------------------------------------------------
def delete_blobs(blobs):
    for blob in blobs:
        blob.delete()


def delete_folder(bucket_name, prefix):
    client = storage.Client()
    blobs = client.list_blobs(bucket_name, prefix=prefix)
    delete_blobs(blobs)


def cleanup_binaries(project_id):
    delete_folder('{}-code'.format(project_id), 'binaries/')


def get_blobs_in_staging(storage_client, project_id, etl_region, table):
    bucket_name = '{}-staging-{}'.format(project_id, etl_region)
    blobs = storage_client.list_blobs(bucket_name)
    return [blob for blob in blobs if table == blob.name[0: blob.name.find('.')]]

# ------------------------------------bigquery functions--------------------------------------------------------------


# bigquery, check if table exists
def exists_table(bigquery_client, dataset_id, table_id):
    from google.cloud.exceptions import NotFound
    dataset = bigquery_client.get_dataset(dataset_id)
    table_ref = dataset.table(table_id)
    try:
        bigquery_client.get_table(table_ref)
        return True
    except NotFound:
        return False


# bigquery, create a table
def create_table(bigquery_client, dataset_id, table_id, schema, partitioned=False, partition_type='DAY'):
    dataset = bigquery_client.get_dataset(dataset_id)
    table_ref = dataset.table(table_id)
    table = bigquery.Table(table_ref, schema=schema)
    if partitioned:
        table.partitioning_type = partition_type
    table = bigquery_client.create_table(table)
    logging.info("Creating table: {}".format(table_id))
    assert table.table_id == table_id


# create the schema_manager table
def create_schema_management_table(bigquery_client, dataset_id):
    schema = [
        bigquery.SchemaField('table_name', 'STRING', mode='required'),
        bigquery.SchemaField('version', 'INTEGER', mode='required'),
        bigquery.SchemaField('version_date', 'TIMESTAMP', mode='required'),
        bigquery.SchemaField('version_schema', 'STRING', mode='required')
    ]
    create_table(bigquery_client, dataset_id, 'schema_management', schema)


# bigquery, create schema_management table if not exists
def create_schema_management_table_if_not_exits(bigquery_client, dataset_id):
    if not exists_table(bigquery_client, dataset_id, 'schema_management'):
        create_schema_management_table(bigquery_client, dataset_id)


# get any table schema from BigQuery
def get_table_schema(bigquery_client, dataset_id, table_id):
    dataset = bigquery_client.get_dataset(dataset_id)
    table_ref = dataset.table(table_id)
    table = bigquery_client.get_table(table_ref)
    return table.schema


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


def save_table_version_to_schema_management_table(bigquery_client, dataset_id, table_id, version, version_schema):
    dataset_ref = bigquery_client.dataset(dataset_id)
    dataset = bigquery_client.get_dataset(dataset_ref.dataset_id)
    table_ref = dataset.table('schema_management')
    table = bigquery_client.get_table(table_ref)
    rows_to_insert = [
        (table_id, version, datetime.datetime.now(), str(version_schema))
    ]
    errors = bigquery_client.insert_rows(table, rows_to_insert)  # API request
    logging.info("Schema_management table updated for table: {}, version: {}".format(table_id, version))
    assert errors == []


def manage_table_schemas(bigquery_client, dataset_id, table_id, blob):
    dataset_ref = bigquery_client.dataset(dataset_id)
    dataset = bigquery_client.get_dataset(dataset_ref.dataset_id)

    # get staging table
    table_ref = dataset.table('{}_staging'.format(table_id))
    staging_table = bigquery_client.get_table(table_ref)

    # get table information from manage_schema table
    table_row_data = get_table_latest_version_data(bigquery_client, dataset_id, table_id)

    if table_row_data is not None:  # table already exists
        table_version = table_row_data.last_version
        version_schema = table_row_data.version_schema
        # compare schema to check if we need to create a new version
        if version_schema != str(staging_table.schema):
            logging.info("New schema detected for table: {}".format(table_id))
            # create a new table version with accumulated schema
            create_table(bigquery_client, dataset_id, '{}_v{}'.format(table_id, table_version + 1), staging_table.schema, partitioned=True, partition_type='DAY')
            # save data to manage_schema_table
            save_table_version_to_schema_management_table(bigquery_client, dataset_id, table_id, table_version + 1, staging_table.schema)

    else:  # table do not exist in database
        # create table version 1 with staging schema
        create_table(bigquery_client, dataset_id, '{}_v1'.format(table_id), staging_table.schema, partitioned=True, partition_type='DAY')
        # save data to manage_schema_table
        save_table_version_to_schema_management_table(bigquery_client, dataset_id, table_id, 1, staging_table.schema)


# remove staging tables
def remove_staging_table(bigquery_client, project_id, dataset_id, table_id):
    try:
        staging_table = bigquery_client.get_table('{}.{}.{}_staging'.format(project_id, dataset_id, table_id))
        logging.info('Deleting staging table: `{}`'.format(staging_table.table_id))
        bigquery_client.delete_table(staging_table)
    except Exception as e:
        pass


# save blobs to staging tables
def save_blob_to_bigquery_staging_table(bigquery_client, project_id, dataset_id, table_id, blob, etl_region):
    # remove staging table if exists
    remove_staging_table(bigquery_client, project_id, dataset_id, table_id)

    dataset_ref = bigquery_client.dataset(dataset_id)
    dataset = bigquery_client.get_dataset(dataset_ref.dataset_id)

    job_config = bigquery.LoadJobConfig()
    job_config.source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
    job_config.autodetect = True
    uri = "gs://{}-staging-{}/{}".format(project_id, etl_region, blob.name)

    load_job = bigquery_client.load_table_from_uri(
        uri,
        dataset_ref.table("{}_staging".format(table_id)),
        location=dataset.location,
        job_config=job_config,
    )  # API request
    logging.info("Starting job: `{}` to load data into staging table: `{}` to get the schema".format(load_job.job_id, '{}_staging'.format(table_id)))

    load_job.result()
    logging.info("Job finished.")

    destination_table = bigquery_client.get_table(dataset_ref.table('{}_staging'.format(table_id)))
    logging.info("Loaded `{}` rows into staging table: `{}`.".format(destination_table.num_rows, '{}_staging'.format(table_id)))


# save blobs to versioned tables
def save_blob_to_bigquery_versioned_table(bigquery_client, project_id, dataset_id, table_id, blob, etl_region):

    dataset_ref = bigquery_client.dataset(dataset_id)
    dataset = bigquery_client.get_dataset(dataset_ref.dataset_id)

    # get corresponding table version information
    table_row_data = get_table_latest_version_data(bigquery_client, dataset_id, table_id)
    table_name = '{}_v{}'.format(table_row_data.table_name, table_row_data.last_version)

    job_config = bigquery.LoadJobConfig()
    job_config.source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
    job_config.schema = get_table_schema(bigquery_client, dataset_id, table_name)
    uri = "gs://{}-staging-{}/{}".format(project_id, etl_region, blob.name)

    load_job = bigquery_client.load_table_from_uri(
        uri,
        dataset_ref.table(table_name),
        location=dataset.location,
        job_config=job_config,
    )  # API request
    logging.info(
        "Starting job: `{}` to load data into versioned table: `{}`.".format(load_job.job_id, table_name))

    load_job.result()
    logging.info("Job finished.")

    destination_table = bigquery_client.get_table(dataset_ref.table(table_name))
    logging.info("There are `{}` rows in versioned table: `{}`.".format(destination_table.num_rows, table_name))


# ---------------------------- pubsub fucntions -------------------------------------------------------------

def publish_to_pubsub(element, project, dest_dataset, table, etl_region):
    import logging
    from google.cloud import pubsub_v1
    logging.getLogger().setLevel(logging.INFO)
    post_processing_topic = 'post-dataflow-processing-topic'
    logging.info("Sending message to projects/{}/topics/{}".format(project, post_processing_topic))
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project, post_processing_topic)
    message = {
        'project': project,
        'dest_dataset': dest_dataset,
        'table': table,
        'etl_region': etl_region,
    }
    data = json.dumps(message).encode('utf-8')
    future = publisher.publish(topic_path, data=data)
    logging.info("Pubsub message Id: {}. Sent message {}".format(future.result(), data))


# --------------------------------------- main ---------------------------------------------------------------
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
    etl_region = message['etl_region'].lower()

    bigquery_client = bigquery.Client(project=project)
    storage_client = storage.Client(project=project)

    # create table for schema management if not exists
    create_schema_management_table_if_not_exits(bigquery_client, dataset)

    # read all blobs from staging -> to an array
    blobs = get_blobs_in_staging(storage_client, project, etl_region, table)

    for blob in blobs:
        try:
            # save blob to bigquery staging table
            save_blob_to_bigquery_staging_table(bigquery_client, project, dataset, table, blob, etl_region)

            # analyze schemas
            manage_table_schemas(bigquery_client, dataset, table, blob)

            # save blob to big query using last table_version
            save_blob_to_bigquery_versioned_table(bigquery_client, project, dataset, table, blob, etl_region)

            # delete staging table related to the table
            remove_staging_table(bigquery_client, project, dataset, table)

            # delete blob from staging bucket
            blob.delete()

        except Exception as e:
            logging.error("Error loading blob: {} to staging table: {}.{}_staging".format(blob.name, dataset, table))
            logging.info("Sending pubsub message to handle error for blob: {}".format(blob.name))
            # todo send pubsub message

    # clean up binaries
    cleanup_binaries(project)

# to debug locally
if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    # go to https://www.base64encode.org/
    # encode json object according to project
    # {"project": "c39-txf-sandbox", "dest_dataset": "main_dwh", "etl_region": "US"}
    # event = {
    #     'data': 'eyJwcm9qZWN0IjogImMzOS10eGYtc2FuZGJveCIsICJyZWdpb24iOiAidXMtZWFzdDEiLCAiZGVzdF9kYXRhc2V0IjogIm1haW5fZHdoIiwgImV0bF9yZWdpb24iOiAiVVMifQ=='
    # }

    #{"project": "taxfyle-qa-data", "dest_dataset": "data_warehouse_us", "table" : "job_event", "etl_region": "US"}
    event ={
        'data' : 'eyJwcm9qZWN0IjogInRheGZ5bGUtcWEtZGF0YSIsICJkZXN0X2RhdGFzZXQiOiAiZGF0YV93YXJlaG91c2VfdXMiLCAidGFibGUiIDogImpvYl9ldmVudCIsICJldGxfcmVnaW9uIjogIlVTIn0='
    }

    context = {}
    main(event, context)
