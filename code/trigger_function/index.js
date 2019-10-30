const { google } = require('googleapis');
const dataflow = google.dataflow('v1b3');

const TEMPLATE_BUCKET = 'c39-txf-sandbox-code'; //"taxfyle-qa-data-code" //'c39-txf-sandbox-code';
const project = "c39-txf-sandbox"; //"taxfyle-qa-data"; //"c39-txf-sandbox"

exports.executeTemplateInDataflow = (req, res) => {

  console.log('Starting dataflow template trigger');   
  console.log(req);

  var jobName = 'trigger-pipeline-template';
  var tmpLocation = `gs://${TEMPLATE_BUCKET}/tmp`;
  var templatePath = `gs://${TEMPLATE_BUCKET}/templates/pipeline-template`;
  var request = {
    projectId: process.env.GCLOUD_PROJECT,
    location: 'us-east1', //'us-central1', //'us-east1'
    requestBody: {
      jobName: jobName,
      parameters: {
        db_host : "10.8.240.3",
        db_port : "5432",
        db_user : "txf-user", 
        db_password : "Qwerty123",
        dest_dataset: "main_dwh",
        dest_bucket: "c39-txf-sandbox-datalake", //"taxfyle-qa-data-datalake", //"c39-txf-sandbox-datalake",
        etl_region: "US"
      },
      environment: {
        tempLocation: tmpLocation
      }
    },
    gcsPath: templatePath
  }
  
  console.log (request);
  
   google.auth.getClient({
      scopes: ['https://www.googleapis.com/auth/cloud-platform']
    })
    .then(auth => {
  
     console.log('we are here (again)!!');
     
     request.auth = auth;
     
     dataflow.projects.locations.templates.launch(request);
     
      res.status(200).send("Finishing function. Sending info as response");
    })
    .catch(error => {
      console.error(error);
     
     res.status(500).send(error);
    });
}