There are 2 types of use cases:
1. Load testing by creating a custom locustfile.py
2. Data generation using an existing model found in models dir and using locustfile-faker.py

#########

For local testing, run the following commands:

python3 -m venv locust-env
source locust-env/bin/activate
python -m pip install -r requirements.txt
locust -f locustfile.py or locust -f locustfile-faker.py
deactivate
