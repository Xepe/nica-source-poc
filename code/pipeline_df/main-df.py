import argparse
import datetime
import logging
import apache_beam as beam
from beam_nuggets.io import relational_db
from apache_beam.options.pipeline_options import GoogleCloudOptions, PipelineOptions, SetupOptions, StandardOptions, WorkerOptions
import base64

db_schemas = [   
                # {
                #     'database': 'txf-data', 
                #     'tables' : [ 
                #         {
                #             'name' : 'data',
                #             'schema' : ('id:INTEGER, text:STRING, etl_region:STRING, etl_date_updated:TIMESTAMP')
                #         }

                #     ] 
                # }


                # taxfyle

                { 
                    'database': 'billing',
                    'tables': [
                                {
                                    'name': 'billing_method',
                                    'schema': ('id:INTEGER, billing_profile_id:INTEGER, workspace_id:INTEGER, type:STRING, user_id:STRING, date_created:TIMESTAMP, date_modified:TIMESTAMP, data:STRING, metadata:STRING, team_id:STRING, inactive:BOOL, limit:INTEGER, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name': 'billing_profile',
                                    'schema': ('id:INTEGER, user_id:STRING, workspace_id:INTEGER, date_created:TIMESTAMP, date_modified:TIMESTAMP, metadata:STRING, default_billing_method_id:INTEGER, default_payout_method_id:INTEGER, team_id:STRING, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name': 'coupon',
                                    'schema': ('id:INTEGER, code:STRING, workspace_id:INTEGER, friendly_name:STRING, description:STRING, max_total_redemptions:INTEGER, date_expires:TIMESTAMP, duration:STRING, coupon_type:STRING, referrer_user_id:STRING, created_by_user_id:STRING, off_type:STRING, percent_off:FLOAT, amount_off:FLOAT, date_created:TIMESTAMP, date_modified:TIMESTAMP, max_amount_off:FLOAT, max_percent_off:FLOAT, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name': 'user_coupon',
                                    'schema': ('id:INTEGER, coupon_id:INTEGER, user_id:STRING, redeemed:BOOL, date_redeemed:TIMESTAMP, date_created:TIMESTAMP, date_modified:TIMESTAMP, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name': 'credit_transactions',
                                    'schema': ('id:INTEGER, transaction_type:STRING, amount:INT64, billing_method_id:NUMERIC, version:INT64, date_created:TIMESTAMP, metadata:STRING, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name': 'payout_method',
                                    'schema': ('id:INTEGER, billing_profile_id:INTEGER, workspace_id:INTEGER, type:STRING, user_id:STRING, date_created:TIMESTAMP, date_modified:TIMESTAMP, data:STRING, metadata:STRING, team_id:STRING, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                    ]
                },

                { 
                    'database': 'documents',
                    'tables': [
                                {
                                    'name': 'document',
                                    'schema': ('id:INTEGER, title:STRING, description:STRING, owner_id:STRING, workspace_id:STRING, archived:BOOL, date_created:TIMESTAMP, date_modified:TIMESTAMP, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name':'document_access',
                                    'schema': ('id:INTEGER, grantor_id:STRING,type:STRING, job_id:STRING, edit_permission:STRING, date_created:TIMESTAMP, date_modified:TIMESTAMP, document_id:INTEGER, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name': 'document_tag',
                                    'schema': ('id:INTEGER, document_id:INTEGER, tag_id:INTEGER, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name':'document_version',
                                    'schema':('id:INTEGER, files:STRING, date_created:TIMESTAMP, author_id:STRING, message:STRING, document_id:INTEGER, purged:BOOL, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name':'tag',
                                    'schema':('id:INTEGER, label:STRING, color:STRING, workspace_id:STRING, date_created:TIMESTAMP, date_modified:TIMESTAMP, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                    ]
                },

                { 
                    'database':'iam',
                    'tables': [
                                {
                                    'name':'device',
                                    'schema':('id:INTEGER, date_created:TIMESTAMP,  date_modified:TIMESTAMP, user_id:STRING, enabled:BOOL, data:STRING, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name':'invitation',
                                    'schema':('id:INTEGER, date_created:TIMESTAMP, date_modified:TIMESTAMP, email:STRING, token:STRING, workspace_id:INTEGER, workspace_role_id:INTEGER, team_id:INTEGER, team_role_id:INTEGER, expires:TIMESTAMP, created_by_user_id:STRING, status:STRING, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name':'role',
                                    'schema':('id:INTEGER, date_created:TIMESTAMP, date_modified:TIMESTAMP, workspace_id:INTEGER, name:STRING, description:STRING, is_owner_role:BOOL, permissions:STRING, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name':'role_member',
                                    'schema':('id:INTEGER, date_created:TIMESTAMP, date_modified:TIMESTAMP, member_id:INTEGER, role_id:INTEGER, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name':'skill',
                                    'schema':('id:INTEGER, date_created:TIMESTAMP, date_modified:TIMESTAMP, workspace_id:INTEGER, name:STRING, description:STRING, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name':'skill_member',
                                    'schema':('id:INTEGER, date_created:TIMESTAMP, date_modified:TIMESTAMP, member_id:INTEGER, skill_id:INTEGER, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name':'team',
                                    'schema':('id:INTEGER, date_created:TIMESTAMP, date_modified:TIMESTAMP, slug:STRING, name:STRING, owner_id:STRING, group_chat_conversation_id:INTEGER, inactive:BOOL, workspace_id:INTEGER, picture:STRING, address:STRING, team_purpose:STRING, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name':'team_member',
                                    'schema':('id:INTEGER, date_created:TIMESTAMP, date_modified:TIMESTAMP, workspace_id:INTEGER, team_id:INTEGER, user_id:STRING, inactive:BOOL, team_role_id:INTEGER, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name':'team_role',
                                    'schema':('id:INTEGER,  date_created:TIMESTAMP, date_modified:TIMESTAMP, workspace_id:INTEGER, name:STRING, is_owner_role:BOOL, description:STRING, permissions:STRING, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name':'workspace',
                                    'schema':('id:INTEGER, date_created:TIMESTAMP, date_modified:TIMESTAMP, slug:STRING, name:STRING, branding:STRING, config:STRING,  default_role_id:INTEGER, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name':'workspace_domain',
                                    'schema':('id:INTEGER, date_created:TIMESTAMP, date_modified:TIMESTAMP, workspace_id:INTEGER, domain:STRING, target:STRING, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name':'workspace_member',
                                    'schema':('id:INTEGER, date_created:TIMESTAMP, date_modified:TIMESTAMP, workspace_id:INTEGER, user_id:STRING, given_name:STRING, family_name:STRING, email:STRING, picture:STRING, phone:STRING, inactive:BOOL, max_concurrent_provider_jobs:INTEGER, member_permissions:STRING, notification_preferences:STRING, approved_terms_version:STRING, referrer:STRING, referrer_metadata:STRING, member_metadata:STRING, workspace_metadata:STRING, last_login:TIMESTAMP, last_seen:TIMESTAMP, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                    ]
                },

                { 
                    'database': 'jobs',
                    'tables': [
                                {
                                    'name': 'job',
                                    'schema': ('id:STRING, workspace_id:STRING, answers:STRING, status:STRING, name:STRING, description:STRING, years:STRING, coverage_states:STRING, layerConversation:STRING, created_by:STRING, current_milestone_id:STRING, date_transmitted:TIMESTAMP, date_created:TIMESTAMP, date_start:TIMESTAMP, date_modified:TIMESTAMP, date_accepted:TIMESTAMP, date_closed:TIMESTAMP, date_reopened:TIMESTAMP, latest_paid_date:TIMESTAMP, paid_date:TIMESTAMP, primary_amount:FLOAT, federal_amount:FLOAT, state_amount:FLOAT, admin_fee_amount:FLOAT, gross_amount:FLOAT, coupon_amount:FLOAT, amended_amount:FLOAT, total:FLOAT, paid_amount:FLOAT, provider_cut_amount:FLOAT, provider_cut:FLOAT, latest_paid_amount:FLOAT, fees:STRING, coupon_ids:STRING, coupon_codes:STRING, amendments:STRING, job_specs:STRING, billing_type:STRING, stripe_charges:STRING, members:STRING, milestones:STRING, task_responses:STRING, info_lines:STRING, rating_submitted:INTEGER,rating_submitted_categories:STRING, rating_submitted_comment:STRING, rating_received:INTEGER, rating_received_categories:STRING, rating_received_comment:STRING, schema:INTEGER, owner_team_id:INTEGER, team_ids:STRING, legend_id:STRING, legend_name:STRING, legend_version:INTEGER, date_deadline:TIMESTAMP, stale:BOOL, purge_status:STRING, archived:BOOL, resolution:STRING, resolution_reason:STRING, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name': 'job_event',
                                    'schema': ('id:STRING, date_created:TIMESTAMP, event_type:STRING, event_visibility:STRING, job_id:STRING, description:STRING, triggered_by:STRING, data:STRING, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name': 'legend_cache',
                                    'schema': ('legend_version_id:STRING, legend_data:STRING, etl_region:STRING,etl_date_updated:TIMESTAMP')
                                },
                    ]
                },

                {
                    'database': 'legends',
                    'tables': [
                                {
                                    'name':'legend',
                                    'schema':('id:STRING, workspace_id:STRING, inactive:BOOL, deactivated_by_id:STRING, date_deactivated:TIMESTAMP, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name':'legend_version',
                                    'schema':('id:STRING, legend_id:STRING, version:INTEGER, version_notes:STRING, name:STRING, description:STRING, published:BOOL, date_created:TIMESTAMP, date_modified:TIMESTAMP, date_published:TIMESTAMP, last_updated_by_id:STRING, view_order:INTEGER, concurrency_version:INTEGER, engine_version:STRING, data:STRING, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                    ]
                },

                {
                    'database': 'messages',
                    'tables': [
                                {
                                    'name':'conversation',
                                    'schema':('id:INTEGER, workspace_id:INTEGER, name:STRING, created_by_user_id:STRING, active:BOOL, external_id:STRING, meta:STRING, date_created:TIMESTAMP, date_modified:TIMESTAMP, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name': 'conversation_participant',
                                    'schema':('id:INTEGER, conversation_id:INTEGER, user_id:STRING, active:BOOL, type:STRING, last_seen:TIMESTAMP, date_created:TIMESTAMP, date_modified:TIMESTAMP, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name':'message',
                                    'schema':('id:INTEGER, conversation_id:INTEGER, user_id:STRING, content:STRING, mentions:STRING, active:BOOL, date_created:TIMESTAMP, date_modified:TIMESTAMP, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                },
                                {
                                    'name':'message_status',
                                    'schema':('id:INTEGER, message_id:INTEGER, active:BOOL, user_id:STRING, status:STRING, date_created:TIMESTAMP, date_modified:TIMESTAMP, etl_region:STRING, etl_date_updated:TIMESTAMP')
                                }
                    ]
                }
]

def get_db_source_config(pipeline_options, database):

    return relational_db.SourceConfiguration(
            drivername  = 'postgresql+pg8000',
            host        = str(pipeline_options.db_host),
            port        = int(str(pipeline_options.db_port)),
            username    = str(pipeline_options.db_user),
            password    = str(pipeline_options.db_password),
            database    = database
        )

def fix_dates(element, etl_region):
    import datetime
    for key,value in element.items():

        if isinstance(value, datetime.datetime) or isinstance(value, dict) or isinstance(value, list):
            element[key] = str(value)

    now = datetime.datetime.now().isoformat()
    element.update({'etl_region': etl_region, 'etl_date_updated': str(now)})

    print(element.items())

    return element


class UserOptions(PipelineOptions):
    @classmethod
    def _add_argparse_args(cls, parser):
        parser.add_value_provider_argument('--db_host', type=str, dest='db_host', default='no_host')
        parser.add_value_provider_argument('--db_port', type=int, dest='db_port', default=0, required=False)
        parser.add_value_provider_argument('--db_user', type=str, dest='db_user', default='no_user')
        parser.add_value_provider_argument('--db_password', type=str, dest='db_password', default='no_password')
        parser.add_value_provider_argument('--dest_dataset', type=str, dest='dest_dataset', default='no_dataset')
        parser.add_value_provider_argument('--dest_bucket', type=str, dest='dest_bucket', default='no_bucket')
        parser.add_value_provider_argument('--etl_region', type=str, dest='etl_region', default='no_region')


def run(argv=None):
    logging.getLogger().setLevel(logging.DEBUG)
    logging.info("printing arguments")

    """Main entry point; defines and runs the data pipeline."""
    parser = argparse.ArgumentParser()    
    known_args, pipeline_args = parser.parse_known_args(argv)

    print ("conocidos")
    print(known_args)
    print ("pipeline")
    print (pipeline_args)

    # We use the save_main_session option because one or more DoFn's in this
    # workflow rely on global context (e.g., a module imported at module level).
    pipeline_options = UserOptions(pipeline_args)
    # pipeline_options.view_as(SetupOptions).save_main_session = True

    google_cloud_options = pipeline_options.view_as(GoogleCloudOptions)
    project = str(google_cloud_options.project)
    etl_region = str(pipeline_options.etl_region)
    dataset = str(pipeline_options.dest_dataset)
    bucket = str(pipeline_options.dest_bucket)

    timestamp = datetime.datetime.now().isoformat()
    gcp_bucket = 'gs://{}/raw'.format(bucket)

    with beam.Pipeline(options=pipeline_options) as p:

        for d in db_schemas:
            for e in list({"database": d['database'], "table": j} for j in d['tables']):

                print("Processing record: {}".format(e))

                source_config = get_db_source_config(pipeline_options, e['database'])

                records = p | "Reading records from db/table: {}[{}]".format(d['database'], e['table']['name']) \
                    >> relational_db.ReadFromDB(source_config=source_config, table_name=e['table']['name']) \
                    | "Pre-processing pipeline records for: {}[{}]".format(d['database'], e['table']['name']) \
                    >> beam.Map(fix_dates, etl_region)

                records | "Writing records to raw storage for: {}[{}]".format(d['database'], e['table']['name']) \
                    >> beam.io.WriteToText('{}/{}/{}/{}.jsonl'.format(gcp_bucket, e['database'], timestamp, e['table']['name']))

                records | "Writing records to BQ for: {}[{}]".format(d['database'], e['table']['name']) \
                    >> beam.io.WriteToBigQuery(
                         '{}:{}.{}'.format(project, dataset, e['table']['name']),
                          schema=e['table']['schema'],
                         # Creates the table in BigQuery if it does not yet exist.
                         create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                         # Deletes all data in the BigQuery table before writing.
                         write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND)


if __name__ == '__main__':
    run()
