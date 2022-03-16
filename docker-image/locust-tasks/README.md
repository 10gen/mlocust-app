################################################################
# Overview
################################################################
There are 2 types of use cases:
1. Load testing by creating a custom locustfile.py
2. Data generation using an existing model found in models dir and using locustfile-faker.py

################################################################
# For local testing, run the following commands:
################################################################
python3 -m venv locust-env
source locust-env/bin/activate
python -m pip install -r requirements.txt
locust -f locustfile.py or locust -f locustfile-faker.py
deactivate

################################################################
# Creating your own pyfaker model 
################################################################
If you want to create your own model, use models/member.csv.100 as an example. Your model filename must end with the recommended number of bulk inserts a single worker can handle using a single simulated user. You'll have to iteratively check-in codes and test on mLocust till you figure out the right number.

################################################################
# Model Details
# Note that the bulk insert params have not been optimized for
# the mLocust clusters. If you notice that the bulk inserts
# can be better tuned, please let me know.
################################################################
1. member.csv.100: Sample model that has a little bit of everything. It represents member information, e.g. contact info and addresses etc.
2. news_articles_metadata.csv.1000: News article metadata information used to represent news aggregation information.
3. emr_form_def.csv.500 and emr_form_resp.csv.500: Represents EMR (hospital) forms and responses. These 2 models are expected to run at the same time so you'd have to update the locustfile-faker.py to have 2 tasks that each call one of the models.
4. disaster_relief_items.csv.1000: Disaster relief data representing anything that may be helpful for Ukraine efforts 
