import base64
import json
from google.cloud import bigquery
from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError
import logging


def get_blobs_in_staging(storage_client, project_id, etl_region, table):
    bucket_name = '{}-staging-{}'.format(project_id, etl_region)
    blobs = list(storage_client.list_blobs(bucket_name, prefix='{}.jsonl'.format(table)))
    return sorted(blobs, key=lambda blob: blob.name)


# save blobs to versioned tables
def save_blob_to_bigquery_table(bigquery_client, project_id, dataset_id, table_id, blob, etl_region, schema):

    dataset_ref = bigquery_client.dataset(dataset_id)
    dataset = bigquery_client.get_dataset(dataset_ref.dataset_id)

    job_config = bigquery.LoadJobConfig()
    job_config.source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
    job_config.write_disposition = 'WRITE_TRUNCATE'
    job_config.schema = schema
    uri = "gs://{}-staging-{}/{}".format(project_id, etl_region, blob.name)

    load_job = bigquery_client.load_table_from_uri(
        uri,
        dataset_ref.table(table_id),
        location=dataset.location,
        job_config=job_config,
    )  # API request
    logging.info("Starting job: `{}` to load data into table: `{}`.".format(load_job.job_id, table_id))
    load_job.result()
    logging.info("Job `{}` finished. Data loaded to version table: `{}`.".format(load_job.job_id, table_id))
    destination_table = bigquery_client.get_table(dataset_ref.table(table_id))
    logging.info("There are `{}` rows in versioned table: `{}`.".format(destination_table.num_rows, table_id))


def get_staging_schema(bigquery_client, dataset_id, table_id):
    dataset_ref = bigquery_client.dataset(dataset_id)
    dataset = bigquery_client.get_dataset(dataset_ref.dataset_id)
    staging_table_ref = dataset.table('{}_staging'.format(table_id))
    staging_table = bigquery_client.get_table(staging_table_ref)
    return staging_table.schema


# remove staging tables
def remove_staging_table(bigquery_client, project_id, dataset_id, table_id):
    try:
        staging_table = bigquery_client.get_table('{}.{}.{}_staging'.format(project_id, dataset_id, table_id))
        logging.info('Deleting staging table: `{}`'.format(staging_table.table_id))
        bigquery_client.delete_table(staging_table)
    except Exception as e:
        pass  # staging table doesn't exist


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
    storage_client = storage.Client(project=project)

    # read all blobs from staging -> to an array
    blobs = get_blobs_in_staging(storage_client, project, etl_region, table)

    for blob in blobs:
        try:
            # get current schema
            schema = get_staging_schema(bigquery_client,dataset, table)
            
            # save blob to table
            save_blob_to_bigquery_table(bigquery_client, project, dataset, table, blob, etl_region, schema)

            # delete staging table related to the table
            remove_staging_table(bigquery_client, project, dataset, table)

            blob.delete();

        except GoogleCloudError as e:
            logging.error("Error loading blob: `{}` to table: `{}.{}`. Details: {}".format(blob.name, dataset, table, e))
        except Exception as e:
            logging.error("Unknown error. Details: {}".format(e))


# to debug locally
if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    # go to https://www.base64encode.org/
    # encode json object. See example

    # {"project": "taxfyle-qa-data", "dest_dataset": "data_warehouse_us", "table" : "document", "etl_region": "us"}
    event ={
        'data': 'eyJwcm9qZWN0IjogInRheGZ5bGUtcWEtZGF0YSIsICJkZXN0X2RhdGFzZXQiOiAiZGF0YV93YXJlaG91c2VfdXMiLCAidGFibGUiIDogImRvY3VtZW50IiwgImV0bF9yZWdpb24iOiAidXMifQ=='
    }

    context = {}
    main(event, context)
