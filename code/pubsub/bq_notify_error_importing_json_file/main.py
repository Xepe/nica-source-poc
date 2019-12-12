import base64
import logging
import json
import os
from postmarker.core import PostmarkClient


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
    etl_region = message['etl_region']
    details = message['details'].split(",")

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
    """.format(project, etl_region, dataset, table)
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


# to debug locally
if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    # go to https://www.base64encode.org/
    # encode json object. See example

    #{"project": "taxfyle-qa-data", "dest_dataset": "data_warehouse_us", "table" : "job_event", "etl_region": "US"}
    event ={
        'data': 'eyJwcm9qZWN0IjogInRheGZ5bGUtcWEtZGF0YSIsICJkZXN0X2RhdGFzZXQiOiAiZGF0YV93YXJlaG91c2VfdXMiLCAidGFibGUiIDogImpvYl9ldmVudCIsICJldGxfcmVnaW9uIjogIlVTIn0='
    }

    context = {}
    main(event, context)
