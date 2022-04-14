# Overview
There are 2 types of use cases:
1. Load testing by creating a custom locustfile.py
2. Data generation using an existing model found in models dir and using locustfile-faker.py

It's suggested that you copy one of the existing locust file templates and not modify the existing template.

# Local Testing
```
python3 -m venv locust-env

source locust-env/bin/activate

python -m pip install -r requirements.txt

Example executions:
locust -f locustfile.py -H "srv_2ndarypref|db|coll"
locust -f locustfile-faker.py -H "srv_2ndarypref|db|coll|opt_model|opt_batchsize"
locust -f locustfile-faker-custom.py -H "srv_2ndarypref|db|coll|opt_model|opt_batchsize"

deactivate
```

# Create Your Own Pyfaker Model 
If you want to create your own model, use models/_reference.csv as an example.

# Model Details
0. _reference.csv: This is the model that showcases a little bit of everything. Use this as the starting point.
1. member.csv: Sample model that has a little bit of everything. It represents member information, e.g. contact info and addresses etc.
2. news_articles_metadata.csv: News article metadata information used to represent news aggregation information.
3. emr_form_def.csv and emr_form_resp.csv: Represents EMR (hospital) forms and responses. These 2 models are expected to run at the same time so you'd have to update the locustfile-faker.py to have 2 tasks that each call one of the models.
4. disaster_relief_items.csv: Disaster relief data representing anything that may be helpful for Ukraine efforts 
