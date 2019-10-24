import argparse
import datetime
import logging
import apache_beam as beam
from beam_nuggets.io import relational_db
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions
import pybase64

db_config = {
    'host': '10.8.240.3',
    'port': 5432,
    'user': 'txf-user',
    'password': 'Qwerty123'
}

db_schemas = [   
                {
                    'database': 'txf-data', 
                    'tables' : [ 
                        {
                            'name' : 'data',
                            'schema' : ('id:INTEGER, text:STRING, etl_region:STRING, etl_date_updated:TIMESTAMP')
                        }

                    ] 
                }
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


# def run(request):
#     logging.getLogger().setLevel(logging.DEBUG)
#     logging.info("printing arguments")
#     logging.info(str(request.args))
#     """Main entry point; defines and runs the data pipeline."""
#     parser = argparse.ArgumentParser()    
#     known_args, pipeline_args = parser.parse_known_args(request.args)

#     print ("conocidos")
#     print(known_args)
#     print ("pipeline")
#     print (pipeline_args)

#     # We use the save_main_session option because one or more DoFn's in this
#     # workflow rely on global context (e.g., a module imported at module level).
#     pipeline_options = PipelineOptions(pipeline_args)
#     pipeline_options.view_as(SetupOptions).save_main_session = True

#     timestamp = datetime.datetime.now().isoformat()
#     gcp_bucket = 'gs://c39-txf-sandbox-datalake/raw' 

#     with beam.Pipeline(options=PipelineOptions()) as p:

#         for d in db_schemas:
#             for e in list({"database": d['database'], "table": j} for j in d['tables']):

#                 print("Processing record: {}".format(e))

#                 source_config = get_db_source_config(e['database'])

#                 records = p | "Reading records from db/table: {}[{}]".format(d['database'], e['table']['name']) \
#                     >> relational_db.ReadFromDB(source_config=relational_db.SourceConfiguration(
#             drivername='postgresql+pg8000',
#             host=db_config['host'],
#             port=db_config['port'],
#             username=db_config['user'],
#             password=db_config['password'],
#             database=e['database'],
#         ), table_name=e['table']['name']) \
#                     | "Pre-processing pipeline records for: {}[{}]".format(d['database'], e['table']['name']) \
#                     >> beam.Map(fix_dates)

#                 records | "Writing records to raw storage for: {}[{}]".format(d['database'], e['table']['name']) \
#                     >> beam.io.WriteToText('{}/{}/{}/{}.jsonl'.format(gcp_bucket, e['database'], timestamp, e['table']['name']))

#                 records | "Writing records to BQ for: {}[{}]".format(d['database'], e['table']['name']) \
#                     >> beam.io.WriteToBigQuery(
#                          'c39-txf-sandbox:main_dwh.{}'.format(e['table']['name']),
#                         #'taxfyle-qa-data:txf_dwh.{}'.format(e['table']['name']),
#                           schema=e['table']['schema'],
#                          # Creates the table in BigQuery if it does not yet exist.
#                          create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
#                          # Deletes all data in the BigQuery table before writing.
#                          write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND),


def run(event, context):
    logging.getLogger().setLevel(logging.DEBUG)
    # event.ack()
    args = []

    logging.info("printing arguments")
    if 'data' in event:
        args = pybase64.b64decode(event['data']).decode('utf-8').split(" ")            
    logging.info(args)

    logging.info("printing context")
    logging.info(str(context))

    """Main entry point; defines and runs the data pipeline."""
    parser = argparse.ArgumentParser()
    known_args, pipeline_args = parser.parse_known_args(args)


    logging.info ("*********************Argumentos conocidos***********************")
    logging.info (known_args)

    logging.info ("********************Argumentos para el pipeline******************")
    logging.info (pipeline_args)

    # We use the save_main_session option because one or more DoFn's in this
    # workflow rely on global context (e.g., a module imported at module level).
    # pipeline_options = PipelineOptions(pipeline_args)
    # pipeline_options.view_as(SetupOptions).save_main_session = True

    timestamp = datetime.datetime.now().isoformat()
    gcp_bucket = 'gs://c39-txf-sandbox-datalake/raw' 

    # with beam.Pipeline(options=PipelineOptions()) as p:
    with beam.Pipeline(argv=pipeline_args) as p:

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



if __name__ == '__main__':
    run()
