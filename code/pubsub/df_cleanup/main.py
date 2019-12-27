import base64
import json
from google.cloud import storage
import logging


# -------------------------------------storage functions--------------------------------------------------------------
def delete_blobs(blobs):
    for blob in blobs:
        blob.delete()


def delete_folder(storage_client, bucket_name, prefix):
    blobs = storage_client.list_blobs(bucket_name, prefix=prefix)
    delete_blobs(blobs)


def cleanup_binaries(storage_client, project_id, etl_region):
    delete_folder(storage_client, '{}-code'.format(project_id), 'binaries-{}/'.format(etl_region))


def cleanup_staging_temporal_files(storage_client, project_id, etl_region):
    blobs = storage_client.list_blobs('{}-staging-{}'.format(project_id, etl_region), prefix='beam-temp-')
    delete_blobs(blobs)


# --------------------------------------- main ---------------------------------------------------------------
def main(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
        Args:
             event (dict): Event payload.
             context (google.cloud.functions.Context): Metadata for the event.
        This function receives in event['data']:
        {
          'project'         : 'project_name',
          'etl_region'      : 'etl_region'

        }
    """
    logging.getLogger().setLevel(logging.INFO)
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    logging.info('Received message: {}'.format(pubsub_message))
    message = json.loads(pubsub_message)

    project = message['project']
    etl_region = message['etl_region']

    storage_client = storage.Client(project=project)

    try:
        logging.info("Cleanup binaries for project: `{}` region: `{}` ".format(project, etl_region))
        cleanup_binaries(storage_client, project, etl_region)
        cleanup_staging_temporal_files(storage_client, project, etl_region)
    except Exception as e:
        logging.error("Unknown error. Details: {}".format(e))


# to debug locally
if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    # go to https://www.base64encode.org/
    # encode json object. See example

    # {"project": "taxfyle-qa-data", "etl_region": "us"}
    event = {
        'data': 'eyJwcm9qZWN0IjogInRheGZ5bGUtcWEtZGF0YSIsICJldGxfcmVnaW9uIjogInVzIn0='
    }

    context = {}
    main(event, context)
