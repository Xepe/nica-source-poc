const { google } = require('googleapis');
const dataflow = google.dataflow('v1b3');

exports.executeTemplateInDataflow = (req, res) => {
  console.log('Starting dataflow template trigger'); 
  var body = JSON.parse(req.body.toString());
  var now = new Date();
  var request = {
    projectId: process.env.GCLOUD_PROJECT,
    location: body.parameters.network_region,
    requestBody: {
      jobName: `trigger-pipeline-template-${body.parameters.region}`,
      parameters: {
          // 'timestamp': now.toISOString()
      },
      environment: {
        tempLocation: `gs://${body.parameters.template_bucket}/tmp`
      }
    },
    gcsPath: `gs://${body.parameters.template_bucket}/templates/pipeline-template-${body.parameters.region}`
  }
  
  console.log (request);
  
  google.auth.getClient({
      scopes: ['https://www.googleapis.com/auth/cloud-platform']
    })
    .then(auth => {  
     	console.log('Authentication success...');     
     	request.auth = auth;     
     	console.log('Launching template in Dataflow...')
     	dataflow.projects.locations.templates.launch(request);     
      	res.status(200).send("Finishing function. Sending info as response");
    })
    .catch(error => {
      	console.error(error);
     	res.status(500).send(error);
    });
}