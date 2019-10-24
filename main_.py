import argparse
import datetime
import logging
import apache_beam as beam
from beam_nuggets.io import relational_db
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions

db_config = {
    'host': '10.8.240.3',
    'port': 5432,
    'user': 'txf-user',
    'password': 'Qwerty123'
}

db_schemas = [
    
            # {'database': 'billing', 'tables': [
            #     {'name': 'billing_method', 'schema': (
            #         'id:INTEGER, billing_profile_id:INTEGER, workspace_id:INTEGER, type:STRING, user_id:STRING, date_created:TIMESTAMP,'
            #         'date_modified:TIMESTAMP, data:STRING, metadata:STRING, team_id:STRING, inactive:BOOL, '
            #         'limit:INTEGER, etl_region:STRING, etl_date_updated:TIMESTAMP')}
            #     ]},
            {
                'database': 'txf-data', 
                'tables' : [ 
                    {
                        'name' : 'data',
                        'schema' : ('id:INTEGER, text:STRING, etl_region:STRING, etl_date_updated:TIMESTAMP')
                    }

                ] 
            }
                                                 # {'name': 'billing_profile', 'schema': (
                                                 #     'id:NUMERIC, user_id:STRING, workspace_id:NUMERIC, date_created:DATETIME, date_modified:DATETIME,'
                                                 #     'metadata:STRING, default_billing_method_id:NUMERIC, default_payout_method_id:NUMERIC, team_id:STRING,'
                                                 #     'region:STRING, updated_at:DATETIME')},
                                                 # {'name': 'coupon', 'schema': (
                                                 #     'id:NUMERIC, code:STRING, workspace_id:NUMERIC, friendly_name:STRING, description:STRING,'
                                                 #     'max_total_redemptions:NUMERIC, date_expires:DATETIME, duration:STRING, coupon_type:STRING,'
                                                 #     'referrer_user_id:STRING, created_by_user_id:STRING, off_type:STRING, percent_off:FLOAT,'
                                                 #     'amount_off:FLOAT, date_created:DATETIME, date_modified:DATETIME, max_amount_off:FLOAT, max_percent_off:FLOAT,'
                                                 #     'region:STRING, updated_at:DATETIME')},
                                                 # {'name': 'user_coupon', 'schema': (
                                                 #     'id:NUMERIC, coupon_id:NUMERIC, user_id:STRING, redeemed:BOOL, date_redeemed:DATETIME,'
                                                 #     'date_created:DATETIME, date_modified:DATETIME, region:STRING, updated_at:DATETIME')}]},

              # {
              #     'database': 'documents',
              #     'tables': [{
              #         'name': 'document',
              #         'schema': (
              #             'id:INTEGER, title:STRING, description:STRING, owner_id:STRING, '
              #             'workspace_id:STRING, archived:BOOL, date_created:TIMESTAMP, date_modified:TIMESTAMP, '
              #             'etl_region:STRING, etl_date_updated:TIMESTAMP')},
              #                                       {'name':'document_access', 'schema': (
              #               'id:INTEGER, grantor_id:STRING,type:STRING, job_id:STRING, edit_permission:STRING,'
              #               'date_created:TIMESTAMP, date_modified:TIMESTAMP, document_id:INTEGER, etl_region:STRING,'
              #               'etl_date_updated:TIMESTAMP')}
              #     ]
              # },
                                                # 'document_tag', 'document_version',
              #                                      'tag']},
              # {'database': 'iam', 'tables': ['device', 'invitation', 'role', 'role_member', 'skill', 'skill_member',
              #                                'team', 'team_member', 'team_role', 'workspace', 'workspace_domain',
              #                                'workspace_membet']},
              # {'database': 'jobs', 'tables': ['job','job_event', 'legend_cache', 'legend_ref']},
              # {'database': 'legends', 'tables': ['legend', 'legend_version']},
              # {'database': 'messages', 'tables': ['conversation', 'conversation_participant', 'message',
              #                                     'message_status']}},
              ]


def get_db_source_config(database):

    return relational_db.SourceConfiguration(
            drivername='postgresql+pg8000',
            host=db_config['host'],
            port=db_config['port'],
            username=db_config['user'],
            password=db_config['password'],
            database=database,
        )


def fix_dates(element):
    import datetime
    for key,value in element.items():

        if isinstance(value, datetime.datetime) or isinstance(value, dict):
            element[key] = str(value)

    now = datetime.datetime.now().isoformat()
    element.update({'etl_region': 'US', 'etl_date_updated': str(now)})

    print(element.items())

    return element


def run(argv=None):
    logging.info("printing arguments")
    logging.info(str(argv))
    """Main entry point; defines and runs the data pipeline."""
    parser = argparse.ArgumentParser()
    # parser.add_argument('--input',
    #                     dest='input',
    #                     default='gs://dataflow-samples/shakespeare/kinglear.txt',
    #                     help='Input file to process.')
    # parser.add_argument('--output',
    #                     dest='output',
    #                     required=True,
    #                     help='Output file to write results to.')
    known_args, pipeline_args = parser.parse_known_args(argv)

    print ("conocidos")
    print(known_args)
    print ("pipeline")
    print (pipeline_args)

    # We use the save_main_session option because one or more DoFn's in this
    # workflow rely on global context (e.g., a module imported at module level).
    pipeline_options = PipelineOptions(pipeline_args)
    pipeline_options.view_as(SetupOptions).save_main_session = True

    timestamp = datetime.datetime.now().isoformat()
    gcp_bucket = 'gs://c39-txf-sandbox-datalake/raw' 
                #'gs://c39-txf-sandbox/raw' 
                #'gs://taxfyle-qa-data/data/raw'

    with beam.Pipeline(options=PipelineOptions()) as p:

        for d in db_schemas:
            for e in list({"database": d['database'], "table": j} for j in d['tables']):

                print("Processing record: {}".format(e))

                source_config = get_db_source_config(e['database'])

                records = p | "Reading records from db/table: {}[{}]".format(d['database'], e['table']['name']) \
                    >> relational_db.ReadFromDB(source_config=relational_db.SourceConfiguration(
            drivername='postgresql+pg8000',
            host=db_config['host'],
            port=db_config['port'],
            username=db_config['user'],
            password=db_config['password'],
            database=e['database'],
        ), table_name=e['table']['name']) \
                    | "Pre-processing pipeline records for: {}[{}]".format(d['database'], e['table']['name']) \
                    >> beam.Map(fix_dates)

                records | "Writing records to raw storage for: {}[{}]".format(d['database'], e['table']['name']) \
                    >> beam.io.WriteToText('{}/{}/{}/{}.jsonl'.format(gcp_bucket, e['database'], timestamp, e['table']['name']))

                records | "Writing records to BQ for: {}[{}]".format(d['database'], e['table']['name']) \
                    >> beam.io.WriteToBigQuery(
                         'c39-txf-sandbox:main_dwh.{}'.format(e['table']['name']),
                        #'taxfyle-qa-data:txf_dwh.{}'.format(e['table']['name']),
                          schema=e['table']['schema'],
                         # Creates the table in BigQuery if it does not yet exist.
                         create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                         # Deletes all data in the BigQuery table before writing.
                         write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND),
                # records | 'Writing to stdout' >> beam.Map(print)
            #print(e)
        # data = ( p | beam.Create(db_schema)
        #          | DbExtractData(db_config=db_config))


        # source_config = get_db_source_config(db_config, db_schema[0]['database'])
        #
        # records = p | "Reading records from db" >> relational_db.ReadFromDB(
        #             source_config=source_config,
        #             table_name=db_schema[0]['tables'][0],
        #         )
        #
        # records | 'Writing to file' >> beam.io.WriteToText('user_coupon.txt')
        # #records | 'Writing to bucket' >> beam.io.WriteToText('gs://taxfyle-qa-us-data-raw/billing/user_coupon')
        # #records | 'Writing to BQ table' >> beam.io.WriteToBigQuery('table_name', 'schema_name')
        # records | 'Writing to stdout' >> beam.Map(print)

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    run()
