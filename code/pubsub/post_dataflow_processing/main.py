import base64
import json
from google.cloud import storage
from google.cloud import bigquery
from google.cloud.bigquery import TimePartitioning
import logging
import datetime
from google.cloud.exceptions import GoogleCloudError
from bigquery_schema_generator.generate_schema import SchemaGenerator


bq_error_importing_json_file_topic = 'bq-error-importing-json-file'
bq_refresh_table_view_topic = 'bq-refresh-table-view'


# -------------------------------------storage functions--------------------------------------------------------------
def delete_blobs(blobs):
    for blob in blobs:
        blob.delete()


def delete_folder(storage_client, bucket_name, prefix):
    blobs = storage_client.list_blobs(bucket_name, prefix=prefix)
    delete_blobs(blobs)


def cleanup_binaries(storage_client, project_id):
    delete_folder(storage_client, '{}-code'.format(project_id), 'binaries/')


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


# get the last table version info
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


# save table version to schema_management_table
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


# manage table schemas (return schema, last version)
def manage_table_schemas(bigquery_client, dataset_id, table_id, full_load):
    table_version = 0
    dataset_ref = bigquery_client.dataset(dataset_id)
    dataset = bigquery_client.get_dataset(dataset_ref.dataset_id)

    # get table information from manage_schema table
    table_row_data = get_table_latest_version_data(bigquery_client, dataset_id, table_id)

    # when no full_load
    if not full_load:
        if table_row_data is not None:
            versioned_table_ref = dataset.table('{}_v{}'.format(table_id, table_row_data.last_version))
            versioned_table = bigquery_client.get_table(versioned_table_ref)
            return versioned_table.schema, table_row_data.last_version
        else:
            return None, None

    # get staging table
    staging_table_ref = dataset.table('{}_staging'.format(table_id))
    staging_table = bigquery_client.get_table(staging_table_ref)

    if table_row_data is not None:  # table already exists
        table_version = table_row_data.last_version
        versioned_table_ref = dataset.table('{}_v{}'.format(table_id, table_row_data.last_version))
        versioned_table = bigquery_client.get_table(versioned_table_ref)

        # compare schema to check if we need to create a new version
        if str(versioned_table.schema) != str(staging_table.schema):
            logging.info("New schema detected for table: {}".format(table_id))
            table_version = table_version + 1
            # create a new table version with accumulated schema
            create_table(bigquery_client, dataset_id, '{}_v{}'.format(table_id, table_version), staging_table.schema, partitioned=True, partition_type='DAY')
            # save data to manage_schema_table
            save_table_version_to_schema_management_table(bigquery_client, dataset_id, table_id, table_version, staging_table.schema)

    else:  # table do not exist in database
        # create table version 1 with staging schema
        create_table(bigquery_client, dataset_id, '{}_v1'.format(table_id), staging_table.schema, partitioned=True, partition_type='DAY')
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
        pass


# deduce the schema using the entire json file (return the BigQuery Schema)
def deduce_schema(blob):
    generator = SchemaGenerator(keep_nulls=True,quoted_values_are_strings=True)
    schema_map, error_logs = generator.deduce_schema(blob.download_as_string().splitlines())
    schema = generator.flatten_schema(schema_map)
    result = []
    for item in schema:
        fields = bigquery.schema._parse_schema_resource(item) if 'fields' in item else ()
        i = bigquery.schema.SchemaField(name=item['name'], field_type=item['type'], mode=item['mode'], fields=fields)
        result.append(i)
    return result


# check if blod has a valid schema
# def has_valid_schema(blob):
#     from genson import SchemaBuilder
#     valid_schema = True
#
#     builder = SchemaBuilder()
#     json_list = blob.download_as_string().splitlines()
#
#     for obj in json_list:
#         builder.add_object(json.loads(obj))
#
#     json_schema = json.loads(builder.to_json())
#     properties = json_schema['properties']
#
#     def analyze_json_object(obj):
#         valid_schema = True
#         for field_key, field_value in obj['properties'].items():
#             if not valid_schema:
#                 break
#             if 'type' in field_value and field_value['type'] == 'object':
#                 valid_schema = analyze_json_object(field_value)
#             else:
#                 if 'anyOf' in field_value and len([t for t in field_value['anyOf'] if t['type'] != 'null']) > 1:
#                     logging.error("Field: `{}` has multiple types: `{}`".format(field_key, [t['type'] for t in field_value['anyOf'] if t['type'] != 'null']))
#                     return False
#         return valid_schema
#
#     for field_key, field_value in properties.items():
#         if not valid_schema:
#             break
#         if isinstance(field_value, dict):
#             if field_value['type'] == 'object':
#                 valid_schema = analyze_json_object(field_value)
#             else:
#                 if 'anyOf' in field_value and len([t for t in field_value['anyOf'] if t['type'] != 'null']) > 1:
#                     logging.error("Field: `{}` has multiple types: `{}`".format(field_key, [t['type'] for t in field_value['anyOf'] if t['type'] != 'null']))
#                     return False
#     return valid_schema

# Check for schema structure (return errors as array)
def has_valid_schema(blob):
    from genson import SchemaBuilder
    errors = []

    builder = SchemaBuilder()
    json_list = blob.download_as_string().splitlines()

    for obj in json_list:
        builder.add_object(json.loads(obj))

    json_schema = json.loads(builder.to_json())
    properties = json_schema['properties']

    def analyze_json_object(obj, key):
        for field_key, field_value in obj['properties'].items():
            if 'type' in field_value and field_value['type'] == 'object':
                analyze_json_object(field_value, field_key)
            else:
                if 'anyOf' in field_value and len([t for t in field_value['anyOf'] if t['type'] != 'null']) > 1:
                    message = "Field: `{}.{}` has multiple types: `{}`".format(key, field_key, [t['type'] for t in field_value['anyOf'] if t['type'] != 'null'])
                    errors.append(message)
                    # logging.error(message)

    for field_key, field_value in properties.items():
        if isinstance(field_value, dict):
            if field_value['type'] == 'object':
                analyze_json_object(field_value, field_key)
            else:
                if 'anyOf' in field_value and len([t for t in field_value['anyOf'] if t['type'] != 'null']) > 1:
                    message = "Field: `{}` has multiple types: `{}`".format(field_key, [t['type'] for t in field_value['anyOf'] if t['type'] != 'null'])
                    errors.append(message)
                    # logging.error(message)
    return errors


# save blobs to staging tables
def save_blob_to_bigquery_staging_table(bigquery_client, project_id, dataset_id, table_id, blob, etl_region, schema=None):
    # remove staging table if exists
    remove_staging_table(bigquery_client, project_id, dataset_id, table_id)

    dataset_ref = bigquery_client.dataset(dataset_id)
    dataset = bigquery_client.get_dataset(dataset_ref.dataset_id)

    job_config = bigquery.LoadJobConfig()
    job_config.source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
    if schema is None:
        job_config.autodetect = True
    else:
        job_config.schema = schema
    job_config.schema_update_options = ['ALLOW_FIELD_ADDITION']
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
        logging.warning("Autodetection schema failed for blob: `{}`".format(blob.name))
        errors = has_valid_schema(blob)
        if len(errors) == 0:
            logging.info("Blob `{}` has a valid schema. Schema will be computed using the entire file".format(blob.name))
            schema = deduce_schema(blob)
            logging.info("Schema already computed for blob `{}`".format(blob.name))
            save_blob_to_bigquery_staging_table(bigquery_client, project_id, dataset_id, table_id, blob, etl_region, schema=schema)
        else:
            logging.error("Error loading blob: `{}` to staging table: `{}.{}_staging`".format(blob.name, dataset, table_id))
            for error in errors:
                logging.error(error)

            logging.info("Sending pubsub message to move blob: `{}` to errors folder".format(blob.name))
            # send pubsub message to notify error
            publish_to_pubsub(project_id, dataset_id, table_id, etl_region, bq_error_importing_json_file_topic, errors)


# save blobs to versioned tables
def save_blob_to_bigquery_versioned_table(bigquery_client, project_id, dataset_id, table_id, blob, etl_region, schema, version):

    dataset_ref = bigquery_client.dataset(dataset_id)
    dataset = bigquery_client.get_dataset(dataset_ref.dataset_id)

    table_name = '{}_v{}'.format(table_id, version)

    job_config = bigquery.LoadJobConfig()
    job_config.source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
    job_config.time_partitioning = TimePartitioning()  # Default values: Partition by DAY and field _PARTITIONTIME
    job_config.write_disposition = 'WRITE_APPEND'
    job_config.schema = schema
    uri = "gs://{}-staging-{}/{}".format(project_id, etl_region, blob.name)

    load_job = bigquery_client.load_table_from_uri(
        uri,
        dataset_ref.table(table_name),
        location=dataset.location,
        job_config=job_config,
    )  # API request
    logging.info("Starting job: `{}` to load data into table: `{}`.".format(load_job.job_id, table_name))

    load_job.result()
    logging.info("Job `{}` finished. Data loaded to version table: `{}`.".format(load_job.job_id, table_name))

    destination_table = bigquery_client.get_table(dataset_ref.table(table_name))
    logging.info("There are `{}` rows in versioned table: `{}`.".format(destination_table.num_rows, table_name))


# ---------------------------- pubsub functions -------------------------------------------------------------
def publish_to_pubsub(project, dest_dataset, table, etl_region, topic, details=None):
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
        'etl_region': etl_region
    }

    if details is not None:
        message['details'] = details.join()

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
    full_load = message['full_load'] == 'True'

    bigquery_client = bigquery.Client(project=project)
    storage_client = storage.Client(project=project)

    # create table for schema management if not exists
    create_schema_management_table_if_not_exits(bigquery_client, dataset)

    # read all blobs from staging -> to an array
    blobs = get_blobs_in_staging(storage_client, project, etl_region, table)

    for blob in blobs:
        try:
            # delete staging table related to the table
            remove_staging_table(bigquery_client, project, dataset, table)

            if full_load:
                # save blob to bigquery staging table
                save_blob_to_bigquery_staging_table(bigquery_client, project, dataset, table, blob, etl_region)

            # analyze schemas
            schema, version = manage_table_schemas(bigquery_client, dataset, table, full_load)

            if schema:
                # save blob to big query using last table_version
                save_blob_to_bigquery_versioned_table(bigquery_client, project, dataset, table, blob, etl_region, schema, version)

                # delete staging table related to the table
                remove_staging_table(bigquery_client, project, dataset, table)

                # delete blob from staging bucket
                blob.delete()

                # send pubsub message to refresh table views
                publish_to_pubsub(project, dataset, table, etl_region, bq_refresh_table_view_topic)

            else:
                logging.error("Table: `{}` doesn't exist. Can't load deltas".format(table))

        except Exception as e:
            logging.error("Details: {}".format(e))

    # clean up binaries
    # cleanup_binaries(storage_client, project)


# to debug locally
if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    # go to https://www.base64encode.org/
    # encode json object according to project

    # {"project": "c39-txf-sandbox", "dest_dataset": "main_dwh", "etl_region": "US"}
    # event = {
    #     'data': 'eyJwcm9qZWN0IjogImMzOS10eGYtc2FuZGJveCIsICJyZWdpb24iOiAidXMtZWFzdDEiLCAiZGVzdF9kYXRhc2V0IjogIm1haW5fZHdoIiwgImV0bF9yZWdpb24iOiAiVVMifQ=='
    # }

    # {"project": "taxfyle-qa-data", "dest_dataset": "data_warehouse_us", "table" : "job", "etl_region": "US"}
    # event ={
    #     'data': 'eyJwcm9qZWN0IjogInRheGZ5bGUtcWEtZGF0YSIsICJkZXN0X2RhdGFzZXQiOiAiZGF0YV93YXJlaG91c2VfdXMiLCAidGFibGUiIDogImpvYiIsICJldGxfcmVnaW9uIjogIlVTIn0='
    # }

    {"project": "taxfyle-qa-data", "dest_dataset": "data_warehouse_us", "table" : "job_event", "etl_region": "US"}
    event ={
        'data': 'eyJwcm9qZWN0IjogInRheGZ5bGUtcWEtZGF0YSIsICJkZXN0X2RhdGFzZXQiOiAiZGF0YV93YXJlaG91c2VfdXMiLCAidGFibGUiIDogImpvYl9ldmVudCIsICJldGxfcmVnaW9uIjogIlVTIn0='
    }

    context = {}
    main(event, context)
