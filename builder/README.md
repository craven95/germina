Deployer is in 2 steps. 


First we create the docker image with JSON schemas

Then we can deploy, to deploy just run this cmd : 

docker run -d -v ~/Documents/<qid>:/root/Documents/<qid> -p 8000:8000 --name questionnaire germina/<qid>:latest

to create js bundle for survey render, run following command : 
npx esbuild static/form-entry.js   --bundle   --outfile=static/js/form.bundle.js   --minify   --target=es2019   --format=esm   --global-name=SurveyForm

