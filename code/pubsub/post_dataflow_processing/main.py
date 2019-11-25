import base64
import json
from google.cloud import storage
from google.cloud import bigquery
import logging


def main(event, context):
    """Triggered from a message on a Cloud Pub/Sub topic.
        Args:
             event (dict): Event payload.
             context (google.cloud.functions.Context): Metadata for the event.
        This function receives:
        {
          'project' : 'project_name',
          'region' : 'project_region',
          'dest_dataset': dest_dataset,
          'etl_region' : 'etl_region'
        }
    """
    logging.getLogger().setLevel(logging.INFO)
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    logging.info('Received message: {}'.format(pubsub_message))
    message = json.loads(pubsub_message)

    project = message['project']
    project_region = message['region']
    dataset = message['dest_dataset']
    etl_region = message['dest_dataset']

    bigquery_client = bigquery.Client(project=project)
    storage_client = storage.Client(project=project)


# to debug locally
if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    event = {
        'data': 'eyJwcm9qZWN0IjogImMzOS10eGYtc2FuZGJveCIsICJyZWdpb24iOiAidXMtZWFzdDEiLCAiZGVzdF9kYXRhc2V0IjogIm1haW5fZHdoIiwgImV0bF9yZWdpb24iOiAiVVMifQ=='
    }
    context = {}
    main(event, context)
