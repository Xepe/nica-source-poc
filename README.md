# Taxfyle ETL Pipeline

## Overview

1. ETL pipeline is built using Dataflow.
2. Data is read from Cloud SQL Postgres instance(s).
3. Raw data is storead in a Cloud Storage bucket (datalake).
4. Raw data is inserted in BigQuery (DWH).

## Deploying the solution

Infrastructure has been coded (mostly) using Terraform. To create environment, please run:

``
$make tf-apply
``

### Notes
- Please note that the CloudSQL instance is not considered part of the ETL pipeline infrastructure, and it's not captured in Terraform
- The ETL pipeline project in which the Terraform code is invoked need to have a shared VPC connection to the project where the CloudSQL instance is.

## Running the pipeline

The Terraform code creates a virtual machine (`build-pipeline-send-to-dataflow`) that will trigger via a cron job the execution of the pipeline, every 4 hours. This solution is a workaround to using Dataflow templates, due to an issue passing parameters to the Dataflow pipeline. Cron jobs are executed under the `gcp_user` user, within the vm.

### Manually executing the pipeline

If you want to execute the pipeline manually:

1. `ssh` into `build-pipeline-send-to-dataflow`.
2. List the tasks scheduled on the user `gcp_user`:

```
$sudo crontab -l -u gcp_user
0 */6 * * * /usr/bin/python3 /home/gcp_user/main-df.py --runner DataflowRunner --job_name vm-trigger-pipeline-us --service_account_email service-account-data-pipeline@taxfyle-qa-data.iam.gserviceaccount.com --project taxfyle-qa-data --temp_location gs://taxfyle-qa-data-datalake/tmp --staging_location gs://taxfyle-qa-data-code/binaries --subnetwork https://www.googleapis.com/compute/v1/projects/taxfyle-qa/regions/us-central1/subnetworks/default-kubes-us --region us-central1 --requirements_file /home/gcp_user/requirements.txt --db_host 10.248.0.6 --db_port 5432 --db_user postgres --db_password "*******" --dest_dataset main_dwh --dest_bucket taxfyle-qa-data-datalake --etl_region US
```

3. Copy the command part of the task (i.e., remove the cron expression at the beginning), and execute directly on the shell.



