# Overview
There are 2 types of use cases:
1. Bulk inserting lots of data. It's recommended to use locustfile-mimesis.py as a baseline to work off of. It's faster than faker.
2. Running standard loads against a saturated db. Use locustfile.py as a very basic example.

It's suggested that you copy one of the existing locust file templates into a ./dev directory and not modify the existing template.

# Local Testing
```
python3 -m venv locust-env

source locust-env/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Example executions:
locust -f locustfile.py -H "srv_2ndarypref|db|coll"
locust -f locustfile-mimesis.py -H "srv_2ndarypref|db|coll|batchsize"

deactivate
```
