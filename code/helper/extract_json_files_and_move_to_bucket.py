import io
from zipfile import ZipFile
import logging
import json
from collections import namedtuple

from google.cloud import storage

client = storage.Client()


def extract_json_files_and_move_to_bucket(request):
    """ Triggers from http request.
    This cloud function unzip json and pdf files from a given list of prefixes

    prefix:  it represent a string with the filename to unzip
    file_type: it represent the files to unzip, it could be '.json' or '.pdf'
    action: it could be 'unzip' or 'merge', the merge only is used with
    file_type ='.json'
    """
    request_json = request.get_json()

    # 'raw/historical_jobs_2017-2019'
    input_bucket_name = request_json['input_bucket_name']
    output_bucket_name = request_json['output_bucket_name']

    folder_prefix = request_json['unzip_location']
    action = request_json['action']
    prefix = request_json['prefix']  # job-exports_2019-07-23.zip
    file_type = request_json['file_type']

    input_bucket = client.get_bucket(input_bucket_name)
    output_bucket = client.get_bucket(output_bucket_name)

    dataset_name = '{}/{}'.format(folder_prefix, 'dataset.json')
    dataset = []

    if action == 'unzip':
        blobs = input_bucket.list_blobs(prefix=prefix)

        for blob in filter(lambda x: x.name.endswith('.zip'), blobs):
            logging.info('Start to download the file {}'.format(prefix))

            zipfile = blob.download_as_string()

            with ZipFile(io.BytesIO(zipfile)) as zip:
                files = zip.infolist()

                logging.info('Start to process only {}'.format(file_type))
                filtered_files = list(filter(
                    lambda x: x.filename.endswith(file_type), files))

                logging.info('Total files to process {}'.format(
                    len(filtered_files)))

                for file in filtered_files:
                    information = zip.read(file)
                    filename = '{}/{}'.format(folder_prefix, file.filename)

                    output_blob = output_bucket.blob(filename)

                    if not output_blob.exists():
                        output_blob.upload_from_string(information)

        logging.info('Finish unzip: {}'.format(prefix))

    if action == 'merge' and file_type.endswith('.json'):
        blobs = output_bucket.list_blobs()
        json_blobs = list(filter(lambda x: x.name.endswith(file_type), blobs))

        logging.info('Start to process json files')
        logging.info('Total files to process {}'.format(
            len(json_blobs))
        )

        for json_blob in json_blobs:
            json_file = json_blob.download_as_string()

            dataset.append(json.loads(json_file))

        logging.info('Start to convert json files into string')
        dataset_json = json.dumps(dataset)

        logging.info('Start to upload dataset.json')
        dataset_blob = output_bucket.blob(dataset_name)
        dataset_blob.upload_from_string(dataset_json)

        logging.info('Finish merge')

    return f'Done!'


if __name__ == "__main__":

    Request = namedtuple('Request', [
        'get_json'
    ])

    request = Request(
        get_json=lambda: {
            'input_bucket_name': '',
            'output_bucket_name': '',
            'unzip_location': '',
            'action': '',
            'prefix': '',
            'file_type': ''
        }
    )

    extract_json_files_and_move_to_bucket(request)
