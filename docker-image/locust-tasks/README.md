For local testing, run the following commands:

python3 -m venv locust-env
source locust-env/bin/activate
python -m pip install -r requirements.txt
locust -f locustfile.py or locust -f locustfile-faker.py
deactivate
