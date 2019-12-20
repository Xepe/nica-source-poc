import base64
import logging
import json
from google.cloud import storage
from datetime import datetime
import os
from postmarker.core import PostmarkClient


def get_blobs_in_staging(storage_client, project_id, etl_region, table_id):
    bucket_name = '{}-staging-{}'.format(project_id, etl_region)
    blobs = list(storage_client.list_blobs(bucket_name, prefix='{}.jsonl'.format(table_id)))
    return sorted(blobs, key=lambda blob: blob.name)


def move_blobs_to_error_folder(storage_client, project_id, etl_region, table_id):
    # read all table blobs from staging
    blobs = get_blobs_in_staging(storage_client, project_id, etl_region, table_id)
    now = datetime.now().isoformat()
    for blob in blobs:
        source_bucket_name = '{}-staging-{}'.format(project_id, etl_region)
        dest_bucket_name = '{}-datalake-{}'.format(project_id, etl_region)
        source_bucket = storage_client.get_bucket(source_bucket_name)
        dest_bucket = storage_client.get_bucket(dest_bucket_name)
        new_blob = source_bucket.copy_blob(blob, dest_bucket, 'errors/load_to_BQ/{}/{}'.format(now, blob.name))
        logging.warning('`{}/{}` moved to: `{}/{}` due to processing error.'.format(source_bucket.name, blob.name, dest_bucket.name, new_blob.name))
        blob.delete()


def send_notification_email(project_id, dataset_id, etl_region, table, details):
    postmark_token = str(os.environ['POSTMARK_SERVER_API_TOKEN'])
    postmark_from = str(os.environ['POSTMARK_FROM'])
    postmark_to = str(os.environ['POSTMARK_TO'])

    html_body = """
    <html>
    <hr />
    <h2>Error importing json file to BigQuery</h2>
    <h3>Summary</h3>
    <h3>Project:</h3>
    <p style="padding-left: 30px;">{}</p>
    <h3>Region:</h3>
    <p style="padding-left: 30px;">{}</p>
    <h3>Dataset:</h3>
    <p style="padding-left: 30px;">{}</p>
    <h3>Table:</h3>
    <p style="padding-left: 30px;">{}</p>
    <h3>Details:</h3>
    """.format(project_id, etl_region, dataset_id, table)
    for error in details:
        html_body += """
        <p style="padding-left: 30px;">{}</p>
        """.format(error)

    html_body += """</html>"""

    postmark = PostmarkClient(server_token=postmark_token)
    postmark.emails.send(
        From=postmark_from,
        To=postmark_to,
        Subject='Error importing data from table: {} to BigQuery'.format(table),
        HtmlBody=html_body
    )


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
          'etl_region'      : 'etl_region',
          'details'         : 'details'
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
    details = message['details'].split(",")

    storage_client = storage.Client(project=project)

    # move failed blobs
    move_blobs_to_error_folder(storage_client, project, etl_region, table)

    # send the notification email
    # send_notification_email(project, dataset, etl_region, table, details)


# to debug locally
if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    # go to https://www.base64encode.org/
    # encode json object. See example

    # {"project": "taxfyle-staging-data", "dest_dataset": "data_warehouse_aus", "table": "notifications", "etl_region": "aus", "details": "{\"line\": 2, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 14, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 17, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 57, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 70, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 99, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 106, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 117, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 122, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 164, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 195, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 206, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 234, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 238, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 249, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 256, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 266, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 280, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 287, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 303, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 310, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 328, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 346, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 405, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 423, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 447, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 459, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 465, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 479, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 498, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 522, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 531, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 544, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 574, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 589, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 614, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 625, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 630, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 638, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 644, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 653, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 658, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 675, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 683, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 685, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 689, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 699, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 701, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 711, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 719, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 727, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 731, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 740, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 743, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 752, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 767, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 772, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 781, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 784, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 795, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 801, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 807, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 809, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 815, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 823, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 838, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 855, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 918, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 930, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 967, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 1030, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 1076, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 1090, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 1093, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 1095, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 1104, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 1112, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 1115, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 1119, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 1131, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 1134, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 1156, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 1254, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 1261, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 1284, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 1348, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 1350, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 1353, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 1418, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 1442, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 1517, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 1520, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 1530, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 1609, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,NULLABLE,STRING); new=(hard,display_name,REPEATED,STRING)\"},{\"line\": 1640, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"},{\"line\": 1657, \"msg\": \"Ignoring non-RECORD field with mismatched mode: old=(hard,display_name,REPEATED,STRING); new=(hard,display_name,NULLABLE,STRING)\"}"}
    event = {
        'data': 'eyJwcm9qZWN0IjogInRheGZ5bGUtc3RhZ2luZy1kYXRhIiwgImRlc3RfZGF0YXNldCI6ICJkYXRhX3dhcmVob3VzZV9hdXMiLCAidGFibGUiOiAibm90aWZpY2F0aW9ucyIsICJldGxfcmVnaW9uIjogImF1cyIsICJkZXRhaWxzIjogIntcImxpbmVcIjogMiwgXCJtc2dcIjogXCJJZ25vcmluZyBub24tUkVDT1JEIGZpZWxkIHdpdGggbWlzbWF0Y2hlZCBtb2RlOiBvbGQ9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORyk7IG5ldz0oaGFyZCxkaXNwbGF5X25hbWUsUkVQRUFURUQsU1RSSU5HKVwifSx7XCJsaW5lXCI6IDE0LCBcIm1zZ1wiOiBcIklnbm9yaW5nIG5vbi1SRUNPUkQgZmllbGQgd2l0aCBtaXNtYXRjaGVkIG1vZGU6IG9sZD0oaGFyZCxkaXNwbGF5X25hbWUsTlVMTEFCTEUsU1RSSU5HKTsgbmV3PShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpXCJ9LHtcImxpbmVcIjogMTcsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiA1NywgXCJtc2dcIjogXCJJZ25vcmluZyBub24tUkVDT1JEIGZpZWxkIHdpdGggbWlzbWF0Y2hlZCBtb2RlOiBvbGQ9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORyk7IG5ldz0oaGFyZCxkaXNwbGF5X25hbWUsTlVMTEFCTEUsU1RSSU5HKVwifSx7XCJsaW5lXCI6IDcwLCBcIm1zZ1wiOiBcIklnbm9yaW5nIG5vbi1SRUNPUkQgZmllbGQgd2l0aCBtaXNtYXRjaGVkIG1vZGU6IG9sZD0oaGFyZCxkaXNwbGF5X25hbWUsTlVMTEFCTEUsU1RSSU5HKTsgbmV3PShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpXCJ9LHtcImxpbmVcIjogOTksIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiAxMDYsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiAxMTcsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiAxMjIsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiAxNjQsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiAxOTUsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiAyMDYsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiAyMzQsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiAyMzgsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiAyNDksIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiAyNTYsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiAyNjYsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiAyODAsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiAyODcsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiAzMDMsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiAzMTAsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiAzMjgsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiAzNDYsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiA0MDUsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA0MjMsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA0NDcsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA0NTksIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA0NjUsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiA0NzksIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA0OTgsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiA1MjIsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA1MzEsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA1NDQsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiA1NzQsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiA1ODksIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiA2MTQsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA2MjUsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA2MzAsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiA2MzgsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA2NDQsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiA2NTMsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA2NTgsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiA2NzUsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA2ODMsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA2ODUsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA2ODksIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiA2OTksIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA3MDEsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiA3MTEsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiA3MTksIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiA3MjcsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA3MzEsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiA3NDAsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA3NDMsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiA3NTIsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA3NjcsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA3NzIsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiA3ODEsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA3ODQsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA3OTUsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA4MDEsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA4MDcsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiA4MDksIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiA4MTUsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA4MjMsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA4MzgsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiA4NTUsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiA5MTgsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiA5MzAsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiA5NjcsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiAxMDMwLCBcIm1zZ1wiOiBcIklnbm9yaW5nIG5vbi1SRUNPUkQgZmllbGQgd2l0aCBtaXNtYXRjaGVkIG1vZGU6IG9sZD0oaGFyZCxkaXNwbGF5X25hbWUsTlVMTEFCTEUsU1RSSU5HKTsgbmV3PShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpXCJ9LHtcImxpbmVcIjogMTA3NiwgXCJtc2dcIjogXCJJZ25vcmluZyBub24tUkVDT1JEIGZpZWxkIHdpdGggbWlzbWF0Y2hlZCBtb2RlOiBvbGQ9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORyk7IG5ldz0oaGFyZCxkaXNwbGF5X25hbWUsUkVQRUFURUQsU1RSSU5HKVwifSx7XCJsaW5lXCI6IDEwOTAsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiAxMDkzLCBcIm1zZ1wiOiBcIklnbm9yaW5nIG5vbi1SRUNPUkQgZmllbGQgd2l0aCBtaXNtYXRjaGVkIG1vZGU6IG9sZD0oaGFyZCxkaXNwbGF5X25hbWUsTlVMTEFCTEUsU1RSSU5HKTsgbmV3PShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpXCJ9LHtcImxpbmVcIjogMTA5NSwgXCJtc2dcIjogXCJJZ25vcmluZyBub24tUkVDT1JEIGZpZWxkIHdpdGggbWlzbWF0Y2hlZCBtb2RlOiBvbGQ9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORyk7IG5ldz0oaGFyZCxkaXNwbGF5X25hbWUsUkVQRUFURUQsU1RSSU5HKVwifSx7XCJsaW5lXCI6IDExMDQsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiAxMTEyLCBcIm1zZ1wiOiBcIklnbm9yaW5nIG5vbi1SRUNPUkQgZmllbGQgd2l0aCBtaXNtYXRjaGVkIG1vZGU6IG9sZD0oaGFyZCxkaXNwbGF5X25hbWUsTlVMTEFCTEUsU1RSSU5HKTsgbmV3PShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpXCJ9LHtcImxpbmVcIjogMTExNSwgXCJtc2dcIjogXCJJZ25vcmluZyBub24tUkVDT1JEIGZpZWxkIHdpdGggbWlzbWF0Y2hlZCBtb2RlOiBvbGQ9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORyk7IG5ldz0oaGFyZCxkaXNwbGF5X25hbWUsUkVQRUFURUQsU1RSSU5HKVwifSx7XCJsaW5lXCI6IDExMTksIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiAxMTMxLCBcIm1zZ1wiOiBcIklnbm9yaW5nIG5vbi1SRUNPUkQgZmllbGQgd2l0aCBtaXNtYXRjaGVkIG1vZGU6IG9sZD0oaGFyZCxkaXNwbGF5X25hbWUsUkVQRUFURUQsU1RSSU5HKTsgbmV3PShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpXCJ9LHtcImxpbmVcIjogMTEzNCwgXCJtc2dcIjogXCJJZ25vcmluZyBub24tUkVDT1JEIGZpZWxkIHdpdGggbWlzbWF0Y2hlZCBtb2RlOiBvbGQ9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORyk7IG5ldz0oaGFyZCxkaXNwbGF5X25hbWUsUkVQRUFURUQsU1RSSU5HKVwifSx7XCJsaW5lXCI6IDExNTYsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORylcIn0se1wibGluZVwiOiAxMjU0LCBcIm1zZ1wiOiBcIklnbm9yaW5nIG5vbi1SRUNPUkQgZmllbGQgd2l0aCBtaXNtYXRjaGVkIG1vZGU6IG9sZD0oaGFyZCxkaXNwbGF5X25hbWUsTlVMTEFCTEUsU1RSSU5HKTsgbmV3PShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpXCJ9LHtcImxpbmVcIjogMTI2MSwgXCJtc2dcIjogXCJJZ25vcmluZyBub24tUkVDT1JEIGZpZWxkIHdpdGggbWlzbWF0Y2hlZCBtb2RlOiBvbGQ9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORyk7IG5ldz0oaGFyZCxkaXNwbGF5X25hbWUsUkVQRUFURUQsU1RSSU5HKVwifSx7XCJsaW5lXCI6IDEyODQsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiAxMzQ4LCBcIm1zZ1wiOiBcIklnbm9yaW5nIG5vbi1SRUNPUkQgZmllbGQgd2l0aCBtaXNtYXRjaGVkIG1vZGU6IG9sZD0oaGFyZCxkaXNwbGF5X25hbWUsTlVMTEFCTEUsU1RSSU5HKTsgbmV3PShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpXCJ9LHtcImxpbmVcIjogMTM1MCwgXCJtc2dcIjogXCJJZ25vcmluZyBub24tUkVDT1JEIGZpZWxkIHdpdGggbWlzbWF0Y2hlZCBtb2RlOiBvbGQ9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORyk7IG5ldz0oaGFyZCxkaXNwbGF5X25hbWUsTlVMTEFCTEUsU1RSSU5HKVwifSx7XCJsaW5lXCI6IDEzNTMsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiAxNDE4LCBcIm1zZ1wiOiBcIklnbm9yaW5nIG5vbi1SRUNPUkQgZmllbGQgd2l0aCBtaXNtYXRjaGVkIG1vZGU6IG9sZD0oaGFyZCxkaXNwbGF5X25hbWUsTlVMTEFCTEUsU1RSSU5HKTsgbmV3PShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpXCJ9LHtcImxpbmVcIjogMTQ0MiwgXCJtc2dcIjogXCJJZ25vcmluZyBub24tUkVDT1JEIGZpZWxkIHdpdGggbWlzbWF0Y2hlZCBtb2RlOiBvbGQ9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORyk7IG5ldz0oaGFyZCxkaXNwbGF5X25hbWUsUkVQRUFURUQsU1RSSU5HKVwifSx7XCJsaW5lXCI6IDE1MTcsIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiAxNTIwLCBcIm1zZ1wiOiBcIklnbm9yaW5nIG5vbi1SRUNPUkQgZmllbGQgd2l0aCBtaXNtYXRjaGVkIG1vZGU6IG9sZD0oaGFyZCxkaXNwbGF5X25hbWUsTlVMTEFCTEUsU1RSSU5HKTsgbmV3PShoYXJkLGRpc3BsYXlfbmFtZSxSRVBFQVRFRCxTVFJJTkcpXCJ9LHtcImxpbmVcIjogMTUzMCwgXCJtc2dcIjogXCJJZ25vcmluZyBub24tUkVDT1JEIGZpZWxkIHdpdGggbWlzbWF0Y2hlZCBtb2RlOiBvbGQ9KGhhcmQsZGlzcGxheV9uYW1lLE5VTExBQkxFLFNUUklORyk7IG5ldz0oaGFyZCxkaXNwbGF5X25hbWUsUkVQRUFURUQsU1RSSU5HKVwifSx7XCJsaW5lXCI6IDE2MDksIFwibXNnXCI6IFwiSWdub3Jpbmcgbm9uLVJFQ09SRCBmaWVsZCB3aXRoIG1pc21hdGNoZWQgbW9kZTogb2xkPShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpOyBuZXc9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORylcIn0se1wibGluZVwiOiAxNjQwLCBcIm1zZ1wiOiBcIklnbm9yaW5nIG5vbi1SRUNPUkQgZmllbGQgd2l0aCBtaXNtYXRjaGVkIG1vZGU6IG9sZD0oaGFyZCxkaXNwbGF5X25hbWUsUkVQRUFURUQsU1RSSU5HKTsgbmV3PShoYXJkLGRpc3BsYXlfbmFtZSxOVUxMQUJMRSxTVFJJTkcpXCJ9LHtcImxpbmVcIjogMTY1NywgXCJtc2dcIjogXCJJZ25vcmluZyBub24tUkVDT1JEIGZpZWxkIHdpdGggbWlzbWF0Y2hlZCBtb2RlOiBvbGQ9KGhhcmQsZGlzcGxheV9uYW1lLFJFUEVBVEVELFNUUklORyk7IG5ldz0oaGFyZCxkaXNwbGF5X25hbWUsTlVMTEFCTEUsU1RSSU5HKVwifSJ9'
    }

    context = {}
    main(event, context)
