import argparse
import datetime
import logging
import apache_beam as beam
from beam_nuggets.io import relational_db
from apache_beam.options.pipeline_options import GoogleCloudOptions, PipelineOptions, SetupOptions
import simplejson as json
import google.cloud.logging
client = google.cloud.logging.Client()
client.setup_logging()


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
    import os
    path = 'database_table_list.json' if os.name == 'nt' else '/home/gcp_user/database_table_list.json'

    with open(path) as json_file:
        return json.load(json_file)


def get_db_source_config(pipeline_options, database):
    user_options = pipeline_options.view_as(UserOptions)
    return relational_db.SourceConfiguration(
        drivername='postgresql+pg8000',
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
            if key[0].isnumeric() or '.' in key:
                result = False
                break
        return result

    def fix_invalid_key_name(obj):
        for key, value in obj.items():
            # fix numeric key_names
            if key[0].isnumeric():
                del obj[key]
                obj['_{}'.format(key)] = value
            # fix key containing dots
            if '.' in key:
                del obj[key]
                obj['{}'.format(key.replace('.', '_'))] = value
        return obj

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

    def analyze_field(parent, key, value, level):
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) or isinstance(item, list):
                    analyze_field(parent, key, item, level + 1)

        if isinstance(value, dict):
            for k, v in value.items():
                analyze_field(value, k, v, level + 1)

        # fix answers structure in table: job, job_event.  field: answers.answer -> to string array
        if (table_name == 'job' and level == 1 and key == 'answers' and isinstance(value, list)) or \
           (table_name == 'job_event' and level == 3 and key == 'answers' and isinstance(value, list)):
            for answer in parent[key]:
                new_values = []
                if 'answer' in answer:
                    if isinstance(answer['answer'], list):
                        for value in answer['answer']:
                            new_values.append(convert_value_to_string(value))
                    else:
                        new_values.append(convert_value_to_string(answer['answer']))

                    answer['answer'] = new_values

        # fix stripe_charges in tables: job, job_event -> remove null values from array
        if (table_name == 'job' and level == 1 and key == 'stripe_charges' and isinstance(value, list)) or \
           (table_name == 'job_event' and level == 3 and key == 'stripe_charges' and isinstance(value, list)):
            parent[key] = [i for i in value if i]

        # fix repeatable elements with null value
        if (table_name == 'job' and level == 1 and (key == 'rating_received_categories' or key == 'rating_submitted_categories')) or \
           (table_name == 'job_event' and level == 3 and (key == 'rating_received_categories' or key == 'rating_submitted_categories')):
            if value is None:
                parent[key] = []

        # fix encrypted structure in table: message, field: content.text.encrypted -> to string to do not data loss
        if table_name == 'message' and level == 3 and key == 'encrypted':
            parent[key] = str(value)

        # fix empty structs {}, they should be null
        if isinstance(parent[key], dict) and not bool(parent[key]):
            parent[key] = None

    for field_key, field_value in element.items():
        analyze_field(element, field_key, field_value, 1)

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
    logging.info("Sending message to PubSub: `projects/{}/topics/{}`".format(project, topic))
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


def publish_to_cleanup_pubsub(project, etl_region,  topic):
    import logging
    from google.cloud import pubsub_v1
    logging.getLogger().setLevel(logging.INFO)
    logging.info("Sending message to PubSub: `projects/{}/topics/{}`".format(project, topic))
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project, topic)
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
