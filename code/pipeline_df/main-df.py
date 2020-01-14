#!/usr/bin/python3
import argparse
import datetime
import logging
import apache_beam as beam
from beam_nuggets.io import relational_db
from apache_beam.options.pipeline_options import GoogleCloudOptions, PipelineOptions, SetupOptions
import simplejson as json


class UserOptions(PipelineOptions):
    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_value_provider_argument('--db_host', type=str, dest='db_host', default='no_host')
        parser.add_value_provider_argument('--db_port', type=int, dest='db_port', default=0)
        parser.add_value_provider_argument('--db_user', type=str, dest='db_user', default='no_user')
        parser.add_value_provider_argument('--db_password', type=str, dest='db_password', default='no_password')
        parser.add_value_provider_argument('--dest_dataset', type=str, dest='dest_dataset', default='no_dataset')
        parser.add_value_provider_argument('--dest_bucket', type=str, dest='dest_bucket', default='no_bucket')
        parser.add_value_provider_argument('--etl_region', type=str, dest='etl_region', default='no_region')


def load_db_schema():
    path = '/home/gcp_user/database_table_list.json'

    with open(path) as json_file:
        return json.load(json_file)


def get_db_source_config(pipeline_options, database):
    user_options = pipeline_options.view_as(UserOptions)
    return relational_db.SourceConfiguration(
        drivername='postgresql+pg8000',
        # drivername='postgresql+psycopg2',
        host=str(user_options.db_host),
        port=int(str(user_options.db_port)),
        username=str(user_options.db_user),
        password=str(user_options.db_password),
        database=database
    )


def fix_jsons(element):
    def has_valid_fields(obj):
        result = True
        for key, value in obj.items():
            if key[0].isnumeric() or '.' in key or '-' in key:
                result = False
                break
        return result

    def fix_invalid_key_name(obj):
        obj_result = {}
        for key, value in obj.items():
            key_result = key
            if key_result[0].isnumeric():
                key_result = '_{}'.format(key)
            if '.' in key_result:
                key_result = '{}'.format(key_result.replace('.', '_'))
            if '-' in key_result:
                key_result = '{}'.format(key_result.replace('-', '_'))
            obj_result[key_result] = value

        return obj_result

    def convert_invalid_json_to_valid_json(parent, key, value):
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) or isinstance(item, list):
                    convert_invalid_json_to_valid_json(parent, key, item)

        if isinstance(value, dict):
            if has_valid_fields(value):
                for k, v in value.items():
                    convert_invalid_json_to_valid_json(value, k, v)
            else:
                parent[key] = fix_invalid_key_name(value)

    for field_key, field_value in element.items():
        if isinstance(field_value, dict) or isinstance(field_value, list):
            convert_invalid_json_to_valid_json(element, field_key, field_value)

    return element


def fix_other_schema_issues(element, table_name):

    def convert_value_to_string(value):
        if value is None or isinstance(value, bool):
            return json.dumps(value)
        else:
            return str(value)

    def analyze_field(parent, key, value, parent_path):
        path = '{}__{}'.format(parent_path, key) if parent_path else '{}'.format(key)

        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) or isinstance(item, list):
                    analyze_field(parent, key, item, parent_path)

        if isinstance(value, dict):
            for k, v in value.items():
                analyze_field(value, k, v, path)

        # fix 'answers' structure in table: job, job_event, notifications.  field: answers.answer -> to string array
        if key == 'answers' and isinstance(value, list) and \
                (
                        (table_name == 'job' and parent_path is None) or
                        (table_name == 'job_event' and parent_path == 'data__snapshot') or
                        (table_name == 'notifications' and parent_path == 'context__job')
                ):
            for answer in parent[key]:
                new_values = []
                if 'answer' in answer:
                    if isinstance(answer['answer'], list):
                        new_values = [convert_value_to_string(value) for value in answer['answer']]
                    else:
                        new_values.append(convert_value_to_string(answer['answer']))

                    answer['answer'] = new_values

        # fix 'job_specs' in tables: job, job_event. field: job_spects -> to string array
        if key == 'job_specs' and isinstance(value, list) and \
                (
                    (table_name == 'job' and parent_path is None) or
                    (table_name == 'job_event' and
                     (
                             parent_path == 'data' or
                             parent_path == 'data__snapshot'
                     ))
                ):
            parent[key] = [str(v) for v in value]

        # fix 'stripe_charges' in tables: job, job_event -> remove null values from array
        if key == 'stripe_charges' and isinstance(value, list) and \
                (
                    (table_name == 'job' and parent_path is None) or
                    (table_name == 'job_event' and parent_path == 'data__snapshot')
                ):
            parent[key] = [i for i in value if i]

        # fix 'designee' in tables: job, job_event, notifications -> to string
        if key == 'designee' and not isinstance(value, str) and \
                (
                    (table_name == 'job' and parent_path == 'milestones__tasks') or
                    (table_name == 'job_event' and parent_path == 'data__snapshot__milestones__tasks') or
                    (table_name == 'notifications' and parent_path == 'context__job__milestones__tasks')
                ):
            parent[key] = convert_value_to_string(value)

        # fix 'data' in tables: legend_version -> to string (remove when save to BigQuery)
        if key == 'data' and table_name == 'legend_version' and parent_path is None:
            parent[key] = convert_value_to_string(value)

        # fix 'legend' in tables: job_event -> to string
        if key == 'legend' and table_name == 'job_event' and parent_path == 'data__snapshot':
            parent[key] = convert_value_to_string(value)

        # fix 'legend' in tables: notifications -> to string
        if key == 'legend' and table_name == 'notifications' and parent_path == 'context__job':
            parent[key] = convert_value_to_string(value)

        # fix repeatable elements with null value
        if (key == 'rating_received_categories' or key == 'rating_submitted_categories') and \
                (
                    (table_name == 'job' and parent_path is None) or
                    (table_name == 'job_event' and parent_path == 'data__snapshot') or
                    (table_name == 'notifications' and parent_path == 'context__job')
                ) and value is None:
                parent[key] = []

        # fix 'encrypted' structure in table: message, field: content.text.encrypted -> to string to do not data loss
        if key == 'encrypted' and table_name == 'message' and parent_path == 'content__text':
            parent[key] = str(value)

        # fix 'display_name' in table notifications, field: context.sender.display_name -> to string when is array
        if key == 'display_name' and table_name == 'notifications' and isinstance(value, list) and parent_path == 'context__sender':
            parent[key] = str(value[0])

        # fix fields 'utm_medium, utm_source, utm_campaign' in table workspace_member
        if (key == 'utm_medium' or key == 'utm_source' or key == 'utm_campaign') and table_name == 'workspace_member' and (parent_path == 'referrer_metadata' or parent_path == 'workspace_metadata__referrerMeta'):
            if not value or value is None:
                parent[key] = []
            if isinstance(value, str):
                parent[key] = [value]

        # fix field 'cpa_years_experience' in table workspace_member
        if key == 'cpa_years_experience' and table_name == 'workspace_member' and parent_path == 'workspace_metadata':
            parent[key] = str(value)

        # fix field 'agreed_to_terms' in table workspace_member
        if key == 'agreed_to_terms' and table_name =='workspace_member' and parent_path == 'workspace_metadata':
            parent[key] = str(value)

        # fix fields 'rm_olid, rm_var' in table workspace_member
        if (key == 'rm_olid' or key == 'rm_var') and table_name =='workspace_member' and (parent_path == 'referrer_metadata' or parent_path == 'workspace_metadata__referrerMeta'):
            if isinstance(value, list):
                parent[key] = value[0]

        # fix 'cpa_approved' in table workspace_member
        if key == 'cpa_approved' and table_name =='workspace_member' and parent_path == 'workspace_metadata':
            parent[key] = str(value)

        # fix 'cpa_max_concurrent_jobs' in table workspace_member
        if key == 'cpa_max_concurrent_jobs' and table_name =='workspace_member' and parent_path == 'workspace_metadata':
            if isinstance(value, str):
                if not value:
                    parent[key] = 0
                else:
                    parent[key] = int(value)

        # fix fields 'utm_medium, utm_source, utm_campaign' in table job
        if (key == 'utm_medium' or key == 'utm_source' or key == 'utm_campaign') and table_name == 'job' and parent_path == 'members__user__referrer_meta':
            if not value or value is None:
                parent[key] = []
            if isinstance(value, str):
                parent[key] = [value]

        # fix empty structs {}, they should be null
        if isinstance(parent[key], dict) and not bool(parent[key]):
            parent[key] = None

    for field_key, field_value in element.items():
        analyze_field(element, field_key, field_value, None)

    return element


def fix_dates(element):
    import datetime
    #  fix datetimes
    for key, value in element.items():
        if isinstance(value, datetime.datetime):
            element[key] = str(value)
    return element


def add_extra_fields(element, etl_region):
    from datetime import datetime
    # add extra fields
    element.update({'etl_region': etl_region.upper(), 'etl_date_updated': datetime.now().isoformat()})
    return element


def publish_to_pubsub(element, project, dest_dataset, table, etl_region, topic):
    import logging
    from google.cloud import pubsub_v1
    logging.getLogger().setLevel(logging.INFO)
    logging.info("Sending message to PubSub: `projects/{}/topics/{}-{}`".format(project, topic, etl_region))
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project, '{}-{}'.format(topic, etl_region))
    message = {
        'project': project,
        'dest_dataset': dest_dataset,
        'table': table,
        'etl_region': etl_region,
    }
    data = json.dumps(message).encode('utf-8')
    future = publisher.publish(topic_path, data=data)
    logging.info("Pubsub message Id: {}. Sent message {}".format(future.result(), data))


def publish_to_cleanup_pubsub(project, etl_region,  topic):
    import logging
    from google.cloud import pubsub_v1
    logging.getLogger().setLevel(logging.INFO)
    logging.info("Sending message to PubSub: `projects/{}/topics/{}-{}`".format(project, topic, etl_region))
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project, '{}-{}'.format(topic, etl_region))
    message = {
        'project': project,
        'etl_region': etl_region
    }
    data = json.dumps(message).encode('utf-8')
    future = publisher.publish(topic_path, data=data)
    logging.info("Pubsub message Id: {}. Sent message {}".format(future.result(), data))


def run(argv=None):
    logging.getLogger().setLevel(logging.INFO)

    db_schemas = load_db_schema()

    try:
        """Main entry point; defines and runs the data pipeline."""
        parser = argparse.ArgumentParser()
        known_args, pipeline_args = parser.parse_known_args(argv)

        logging.info("Printing arguments")
        logging.info('Known parameters: {}'.format(known_args))
        logging.info('Pipeline parameters: {}'.format(pipeline_args))

        pipeline_options = PipelineOptions(pipeline_args)
        # We use the save_main_session option because one or more DoFn's in this
        # workflow rely on global context (e.g., a module imported at module level).
        pipeline_options.view_as(SetupOptions).save_main_session = True

        google_cloud_options = pipeline_options.view_as(GoogleCloudOptions)
        project = str(google_cloud_options.project)

        user_options = pipeline_options.view_as(UserOptions)
        etl_region = (str(user_options.etl_region))
        dataset = str(user_options.dest_dataset)
        bucket = str(user_options.dest_bucket)

        timestamp = datetime.datetime.now().isoformat()
        gcp_bucket = 'gs://{}/raw'.format(bucket)
        staging_bucket = 'gs://{}-staging-{}'.format(project, etl_region)

        bq_post_dataflow_processing_topic = 'bq-post-dataflow-processing'
        df_cleanup_topic = 'df-cleanup'

        with beam.Pipeline(options=pipeline_options) as p:
            for d in db_schemas:
                for e in list({"database": d['database'], "table": j} for j in d['tables']):
                    logging.info("Processing record: {}".format(e))

                    source_config = get_db_source_config(pipeline_options, e['database'])

                    records = p | "Reading records from db/table: {}[{}]".format(d['database'], e['table']['name']) >> relational_db.ReadFromDB(source_config=source_config, table_name=e['table']['name']) \
                                | "Fixing dates for: {}[{}]".format(d['database'], e['table']['name']) >> beam.Map(fix_dates) \
                                | "Fixing JSON objects for: {}[{}]".format(d['database'], e['table']['name']) >> beam.Map(fix_jsons) \
                                | "Fixing other schema issues for: {}[{}]".format(d['database'], e['table']['name']) >> beam.Map(fix_other_schema_issues, e['table']['name']) \
                                | "Adding extra fields for: {}[{}] ".format(d['database'], e['table']['name']) >> beam.Map(add_extra_fields, etl_region) \
                                | "Converting to valid BigQuery JSON for: {}[{}] ".format(d['database'], e['table']['name']) >> beam.Map(json.dumps)

                    records | "Writing records to raw storage for: {}[{}]".format(d['database'], e['table']['name']) >> beam.io.WriteToText('{}/{}/{}/{}.jsonl'.format(gcp_bucket, e['database'], timestamp, e['table']['name']))

                    records | "Writing records to staging storage for: {}[{}]".format(d['database'], e['table']['name']) >> beam.io.WriteToText('{}/{}.jsonl'.format(staging_bucket, e['table']['name'])) \
                            | "Sending message to PubSub for: {}[{}]".format(d['database'], e['table']['name']) >> beam.Map(publish_to_pubsub, project, dataset, e['table']['name'], etl_region, bq_post_dataflow_processing_topic)

        # clean up binaries
        publish_to_cleanup_pubsub(project, etl_region, df_cleanup_topic)

    except Exception as e:
        logging.error('Error creating pipeline. Details:{}'.format(e))


if __name__ == '__main__':
    run()
