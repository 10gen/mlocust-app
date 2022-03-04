There are 2 types of use cases:
1. Load testing by creating a custom locustfile.py
2. Data generation using an existing model found in models dir and using locustfile-faker.py

If you want to create your own model, use models/member.csv.100 as an example. Your model filename must end with the recommended number of bulk inserts a single worker can handle using a single simulated user. You'll have to iteratively check-in codes and test on mLocust till you figure out the right number.

#########

For local testing, run the following commands:

python3 -m venv locust-env
source locust-env/bin/activate
python -m pip install -r requirements.txt
locust -f locustfile.py or locust -f locustfile-faker.py
deactivate
