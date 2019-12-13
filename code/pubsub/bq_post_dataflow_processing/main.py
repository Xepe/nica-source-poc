import base64
import json
from google.cloud import storage
from google.cloud import bigquery
from google.cloud.bigquery import TimePartitioning, TimePartitioningType, WriteDisposition, SchemaUpdateOption
import logging
from datetime import datetime
from google.cloud.exceptions import GoogleCloudError
from bigquery_schema_generator.generate_schema import SchemaGenerator


class BadBlobSchemaException(Exception):
    pass


bq_error_importing_json_file_topic = 'bq-error-importing-json-file'
bq_create_views_and_cleanup = 'bq-create-views-and-cleanup'

schema_history_table_name = 'schema_history'


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


# bigquery, create a table
def create_table(bigquery_client, dataset_id, table_id, schema, partitioned=False, partition_type=TimePartitioningType.DAY, partition_field=None):
    dataset = bigquery_client.get_dataset(dataset_id)
    table_ref = dataset.table(table_id)
    table = bigquery.Table(table_ref, schema=schema)
    if partitioned:
        table.partitioning_type = partition_type
        table.time_partitioning = TimePartitioning(field=partition_field, type_=partition_type)

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
    create_table(bigquery_client, dataset_id, schema_history_table_name, schema)


# bigquery, create schema_history_table_name table if not exists
def create_schema_management_table_if_not_exits(bigquery_client, dataset_id):
    if not exists_table(bigquery_client, dataset_id, schema_history_table_name):
        create_schema_management_table(bigquery_client, dataset_id)


# get any table schema from BigQuery
def get_table_schema(bigquery_client, dataset_id, table_id):
    dataset = bigquery_client.get_dataset(dataset_id)
    table_ref = dataset.table(table_id)
    table = bigquery_client.get_table(table_ref)
    return table.schema


# get the last table version info
def get_table_latest_version_data(bigquery_client, dataset_id, table_id):
    dataset_ref = bigquery_client.dataset(dataset_id)
    dataset = bigquery_client.get_dataset(dataset_ref.dataset_id)

    query = ('SELECT '
             '  table_name, '
             '  max(version) as last_version, '
             '  version_schema '
             'FROM `{}.{}.{}` '
             'where table_name = @param_table_name '
             'group by table_name, version_schema '
             'order by max(version) desc limit 1'.format(dataset.project, dataset_id, schema_history_table_name))
    timeout = 30  # in seconds
    param_table_name = bigquery.ScalarQueryParameter('param_table_name', 'STRING', table_id)
    job_config = bigquery.QueryJobConfig()
    job_config.query_parameters = [param_table_name]

    query_job = bigquery_client.query(query, job_config=job_config)  # API request - starts the query

    # Waits for the query to finish
    iterator = query_job.result(timeout=timeout)
    rows = list(iterator)
    return rows[0] if len(rows) > 0 else None


# save table version to schema_management_table
def save_table_version_to_schema_management_table(bigquery_client, dataset_id, table_id, version, version_schema):
    dataset_ref = bigquery_client.dataset(dataset_id)
    dataset = bigquery_client.get_dataset(dataset_ref.dataset_id)
    table_ref = dataset.table(schema_history_table_name)
    table = bigquery_client.get_table(table_ref)

    rows_to_insert = [
        (table_id, version, datetime.now(), str(version_schema))
    ]
    errors = bigquery_client.insert_rows(table, rows_to_insert)  # API request
    logging.info("Schema_management table updated for table: {}, version: {}".format(table_id, version))
    assert errors == []


# manage table schemas (return schema, last version)
def manage_table_schemas(bigquery_client, dataset_id, table_id):
    table_version = 0
    dataset_ref = bigquery_client.dataset(dataset_id)
    dataset = bigquery_client.get_dataset(dataset_ref.dataset_id)

    # get table information from manage_schema table
    table_row_data = get_table_latest_version_data(bigquery_client, dataset_id, table_id)

    # get staging table
    staging_table_ref = dataset.table('{}_staging'.format(table_id))
    staging_table = bigquery_client.get_table(staging_table_ref)

    if table_row_data is not None:  # table already exists
        table_version = table_row_data.last_version
        current_table_ref = dataset.table(table_id)
        current_table = bigquery_client.get_table(current_table_ref)

        # compare schema to check if we need to create a new version
        if str(current_table.schema) != str(staging_table.schema):
            logging.info("New schema detected for table: {}".format(table_id))
            table_version = table_version + 1
            # save data to manage_schema_table
            save_table_version_to_schema_management_table(bigquery_client, dataset_id, table_id, table_version, staging_table.schema)

    else:  # table do not exist in database
        table_version = 1
        # save data to manage_schema_table
        save_table_version_to_schema_management_table(bigquery_client, dataset_id, table_id, 1, staging_table.schema)

    return staging_table.schema, table_version


# remove staging tables
def remove_staging_table(bigquery_client, project_id, dataset_id, table_id):
    try:
        staging_table = bigquery_client.get_table('{}.{}.{}_staging'.format(project_id, dataset_id, table_id))
        logging.info('Deleting staging table: `{}`'.format(staging_table.table_id))
        bigquery_client.delete_table(staging_table)
    except Exception as e:
        pass  # staging table doesn't exist


# deduce the schema using the entire json file (return the BigQuery Schema)
def deduce_schema(blob):
    schema_result = []
    generator = SchemaGenerator(keep_nulls=True,quoted_values_are_strings=True)
    schema_map, error_logs = generator.deduce_schema(blob.download_as_string().splitlines())
    if len(error_logs) == 0:
        schema = generator.flatten_schema(schema_map)
        for item in schema:
            fields = bigquery.schema._parse_schema_resource(item) if 'fields' in item else ()
            i = bigquery.schema.SchemaField(name=item['name'], field_type=item['type'], mode=item['mode'], fields=fields)
            schema_result.append(i)
    return schema_result, error_logs


# save blobs to staging tables
def save_blob_to_bigquery_staging_table(bigquery_client, project_id, dataset_id, table_id, blob, etl_region, schema=None, computed_schema=False):
    # remove staging table if exists
    remove_staging_table(bigquery_client, project_id, dataset_id, table_id)

    dataset_ref = bigquery_client.dataset(dataset_id)
    dataset = bigquery_client.get_dataset(dataset_ref.dataset_id)

    job_config = bigquery.LoadJobConfig()
    job_config.source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
    # job_config.schema_update_options = [SchemaUpdateOption.ALLOW_FIELD_ADDITION] #  ['ALLOW_FIELD_ADDITION']
    if schema is None:
        job_config.autodetect = True
    else:
        job_config.schema = schema
    uri = "gs://{}-staging-{}/{}".format(project_id, etl_region, blob.name)

    load_job = bigquery_client.load_table_from_uri(
        uri,
        dataset_ref.table("{}_staging".format(table_id)),
        location=dataset.location,
        job_config=job_config,
    )  # API request
    logging.info("Starting job: `{}` to load data into staging table: `{}` to get the schema".format(load_job.job_id, '{}_staging'.format(table_id)))

    try:
        load_job.result()
        logging.info("Job finished.")
        destination_table = bigquery_client.get_table(dataset_ref.table('{}_staging'.format(table_id)))
        logging.info("Loaded `{}` rows into staging table: `{}`.".format(destination_table.num_rows, table_id))
    except GoogleCloudError as e:
        if schema is not None:
            if not computed_schema:
                save_blob_to_bigquery_staging_table(bigquery_client, project_id, dataset_id, table_id, blob, etl_region)
            else:
                BadBlobSchemaException(e.errors)
        logging.warning("Autodetection schema failed for table: `{}`. Details: {}".format(table_id, e))
        logging.info("Schema will be computed using the entire file: `{}`".format(blob.name))
        schema, errors = deduce_schema(blob)
        if len(errors) == 0:
            logging.info("Schema already computed for table `{}`".format(table_id))
            save_blob_to_bigquery_staging_table(bigquery_client, project_id, dataset_id, table_id, blob, etl_region, schema=schema, computed_schema=True)
        else:
            raise BadBlobSchemaException(errors)


# save blob to current table
def save_blob_to_bigquery_current_table(bigquery_client, project_id, dataset_id, table_id, blob, etl_region, schema):

    dataset_ref = bigquery_client.dataset(dataset_id)
    dataset = bigquery_client.get_dataset(dataset_ref.dataset_id)

    job_config = bigquery.LoadJobConfig()
    job_config.source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
    job_config.write_disposition = WriteDisposition.WRITE_TRUNCATE
    job_config.schema = schema
    uri = "gs://{}-staging-{}/{}".format(project_id, etl_region, blob.name)

    load_job = bigquery_client.load_table_from_uri(
        uri,
        dataset_ref.table(table_id),
        location=dataset.location,
        job_config=job_config,
    )  # API request
    logging.info("Starting job: `{}` to load data into table: `{}`.".format(load_job.job_id, table_id))

    try:
        load_job.result()
        logging.info("Job `{}` finished. Data loaded to version table: `{}`.".format(load_job.job_id, table_id))
        destination_table = bigquery_client.get_table(dataset_ref.table(table_id))
        logging.info("There are `{}` rows in table: `{}`.".format(destination_table.num_rows, table_id))
    except GoogleCloudError as e:
        logging.error("Error loading blob: `{}` to table: `{}.{}`. Details: {}".format(blob.name, dataset, table_id, e))


# ---------------------------- pubsub functions -------------------------------------------------------------
def publish_to_pubsub(project, dest_dataset, table, etl_region, topic, details=None):
    import logging
    from google.cloud import pubsub_v1
    logging.getLogger().setLevel(logging.INFO)
    logging.info("Sending message to PubSub: `projects/{}/topics/{}`".format(project, topic))
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project, topic)

    message = {
        'project': project,
        'dest_dataset': dest_dataset,
        'table': table,
        'etl_region': etl_region
    }

    if details is not None:
        message['details'] = ",".join(details)

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
    etl_region = message['etl_region']

    bigquery_client = bigquery.Client(project=project)
    storage_client = storage.Client(project=project)

    # create table for schema management if not exists
    create_schema_management_table_if_not_exits(bigquery_client, dataset)

    # read all blobs from staging -> to an array
    blobs = get_blobs_in_staging(storage_client, project, etl_region, table)

    for blob in blobs:
        try:
            current_schema = None
            exists = exists_table(bigquery_client, dataset, table)
            if exists:
                current_schema = get_table_schema(bigquery_client, dataset, table)

            # save blob to bigquery staging table
            save_blob_to_bigquery_staging_table(bigquery_client, project, dataset, table, blob, etl_region, current_schema)

            # analyze schemas
            schema, version = manage_table_schemas(bigquery_client, dataset, table)

            # save blob to big query using last table_version
            save_blob_to_bigquery_current_table(bigquery_client, project, dataset, table, blob, etl_region, schema)

            # send pubsub message to refresh table views
            publish_to_pubsub(project, dataset, table, etl_region, bq_create_views_and_cleanup)

        except BadBlobSchemaException as e:
            logging.error("Error loading blob: `{}` to staging table: `{}.{}_staging`".format(blob.name, dataset, table))
            for error in e.args[0]:
                logging.error(error)

            logging.info("Sending pubsub message to move blob: `{}` to errors folder".format(blob.name))
            # send pubsub message to notify error
            # publish_to_pubsub(project, dataset, table, etl_region, bq_error_importing_json_file_topic, e.args[0])

        except Exception as e:
            logging.error("Unknown error. Details: {}".format(e))


# to debug locally
if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    # go to https://www.base64encode.org/
    # encode json object. See example

    # {"project": "taxfyle-qa-data", "dest_dataset": "data_warehouse_us", "table" : "job_event", "etl_region": "us"}
    # event = {
    #     'data': 'eyJwcm9qZWN0IjogInRheGZ5bGUtcWEtZGF0YSIsICJkZXN0X2RhdGFzZXQiOiAiZGF0YV93YXJlaG91c2VfdXMiLCAidGFibGUiIDogImpvYl9ldmVudCIsICJldGxfcmVnaW9uIjogInVzIn0='
    # }

    # {"project": "taxfyle-qa-data", "dest_dataset": "data_warehouse_us", "table" : "job", "etl_region": "us"}
    event = {
        'data': 'eyJwcm9qZWN0IjogInRheGZ5bGUtcWEtZGF0YSIsICJkZXN0X2RhdGFzZXQiOiAiZGF0YV93YXJlaG91c2VfdXMiLCAidGFibGUiIDogImpvYiIsICJldGxfcmVnaW9uIjogInVzIn0='
    }

    context = {}
    main(event, context)
