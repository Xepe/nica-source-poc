import base64
import json
from google.cloud import bigquery
from google.cloud import storage
import logging


# ------------------------------------storage functions--------------------------------------------------------------
def get_blobs_in_staging(storage_client, project_id, etl_region, table):
    bucket_name = '{}-staging-{}'.format(project_id, etl_region)
    blobs = list(storage_client.list_blobs(bucket_name, prefix='{}.jsonl'.format(table)))
    return sorted(blobs, key=lambda blob: blob.name)


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


# remove staging tables
def remove_staging_table(bigquery_client, project_id, dataset_id, table_id):
    if exists_table(bigquery_client, dataset_id, '{}_staging'.format(table_id)):
        staging_table = bigquery_client.get_table('{}.{}.{}_staging'.format(project_id, dataset_id, table_id))
        logging.info('Deleting staging table: `{}`'.format(staging_table.table_id))
        bigquery_client.delete_table(staging_table)


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
            # delete staging table related to the table
            remove_staging_table(bigquery_client, project, dataset, table)

            blob.delete();

        except Exception as e:
            logging.error("Unknown error. Details: {}".format(e))


# to debug locally
if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    # go to https://www.base64encode.org/
    # encode json object. See example

    # {"project": "taxfyle-staging-data", "dest_dataset": "data_warehouse_aus", "table" : "tag", "etl_region": "aus"}
    event ={
        'data': 'eyJwcm9qZWN0IjogInRheGZ5bGUtc3RhZ2luZy1kYXRhIiwgImRlc3RfZGF0YXNldCI6ICJkYXRhX3dhcmVob3VzZV9hdXMiLCAidGFibGUiIDogInRhZyIsICJldGxfcmVnaW9uIjogImF1cyJ9'
    }

    context = {}
    main(event, context)
