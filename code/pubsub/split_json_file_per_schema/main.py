import base64
import json
import logging
from google.cloud import storage
from json_schema import json_schema


# def get_blobs_in_staging(storage_client, project_id, etl_region, table):
#     bucket_name = '{}-staging-{}'.format(project_id, etl_region)
#     blobs = storage_client.list_blobs(bucket_name)
#     return [blob for blob in blobs if table == blob.name[0: blob.name.find('.')]]

def get_blobs_in_staging(storage_client, project_id, etl_region, table):
    bucket_name = '{}-staging-{}'.format(project_id, etl_region)
    blobs = list(storage_client.list_blobs(bucket_name, prefix='{}.jsonl'.format(table)))
    return sorted(blobs, key=lambda blob: blob.name)


def create_new_blobs(bucket, blob, files):
    blobs = []
    i = 1
    for file in files:
        new_blob = bucket.blob(blob_name='{}-{}'.format(blob.name, i))
        new_blob.upload_from_string(data=b'\n'.join(file), content_type='text/plain')
        blobs.append(new_blob)
        i = i + 1
    return blobs


def create_array_per_schema(blob):
    json_list = blob.download_as_string().splitlines()
    files = []
    i = 1
    array = []
    previous_schema = None
    for json_obj in json_list:
        new_schema = json_schema.dumps(json_obj)
        if previous_schema is None or previous_schema == new_schema:
            previous_schema = new_schema
            array.append(json_obj)
        else:
            new_array = list(array)
            files.append(new_array)
            previous_schema = new_schema
            i = i + 1
            array.clear()
            array.append(json_obj)

    # append last array
    files.append(array)
    return files


def publish_to_pubsub(project, dest_dataset, table, etl_region, topic):
    import logging
    from google.cloud import pubsub_v1
    logging.getLogger().setLevel(logging.INFO)
    logging.info("Sending message to projects/{}/topics/{}".format(project, topic))
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project, topic)
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
    """Triggered from a message on a Cloud Pub/Sub topic 'bq-error-importing-json-file'
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

    post_processing_topic = 'post-dataflow-processing-topic'

    storage_client = storage.Client(project=project)
    bucket = storage_client.get_bucket('{}-staging-{}'.format(project, etl_region))
    blobs = get_blobs_in_staging(storage_client, project, etl_region, table)

    for blob in blobs:
        # generate a file per different schema
        files = create_array_per_schema(blob)
        # create new blobs in staging
        create_new_blobs(bucket, blob, files)
        # delete original blob
        blob.delete()

    # send pubsub message to topic 'post-dataflow-processing-topic'
    publish_to_pubsub(project, dataset, table, etl_region, post_processing_topic)
