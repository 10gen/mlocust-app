#!/usr/bin/env python

########################################################################
#
#                    Recommended Usage:
#                    Users: 1 * workers
#                    Host: srv|db|coll|bulksize
#
########################################################################

########################################################################
#
# Many of you like to get fancy by creating separate object classes
# and external file dependencies, e.g. json files, 
# I discourage you from doing that because there are file path
# reference issues that make things difficult when you containerize
# and deploy to gke. Try to keep everything in this 1 file.
# The only exception to this rule are faker models which need to be
# pre-built and tested and checked in.
#
########################################################################

# Allows us to make many pymongo requests in parallel to overcome the single threaded problem
import gevent
_ = gevent.monkey.patch_all()

########################################################################
# Add any additional imports here.
# But make sure to include in requirements.txt
########################################################################
import pymongo
from bson import json_util
from bson.json_util import loads
from bson import ObjectId
from locust import User, events, task, constant, tag, between
import time
from pickle import TRUE
from datetime import datetime, timedelta
import random
from faker import Faker

from bson.decimal128 import Decimal128
from decimal import Decimal
import string

# Custom Class
class FakeObj:

    fake = Faker()

    def create(self):
        return {
            "testName": self.fake.name(),
            "orderNumber": self.fake.bothify(text = "AD-#########"),
            # "orderStatus": random.choice(["open", "shipped", "declined", "unpaid", "returned"]),
            "orderID": self.fake.uuid4(),
            "shard": random.randint(1,25000),
            "orderStatus": "open",
            "orderReference": self.fake.bothify(text = "????????????", letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'),
            "orderDate": self.fake.date_time_between(start_date=datetime(2017, 12, 31)),
            "locale": "en_US",
            "integrator": "storefront",
            "invoiceNumber": self.fake.bothify(text = "########")
        }

########################################################################
# Even though locust is designed for concurrency of simulated users,
# given how resource intensive fakers/bulk inserts are,
# you should only run 1 simulated user / worker else you'll kill the 
# CPU of the workers.
########################################################################
class MetricsLocust(User):
    ########################################################################
    # Class variables. The values are initialized with None
    # till they get set from the actual locust exeuction 
    # when the host param is passed in.
    # DO NOT MODIFY! PASS IN VIA HOST PARAM.
    ########################################################################
    # DO NOT MODIFY! PASS IN VIA HOST PARAM.
    client, coll, audit, bulk_size, gen = None, None, None, None, FakeObj()

    ####################################################################
    # Unlike a standard locust file where we throttle requests on a per
    # second basis, since we are trying to load data asap, there will 
    # be no throttling
    ####################################################################

    def __init__(self, parent):
        super().__init__(parent)

        # We can't put this in the singleton because we can't modify the params after it's been run once, 
        # e.g. run new test with a different host param
        # Parse out env variables from the host
        vars = self.host.split("|")
        srv = vars[0]
        print("SRV:",srv)
        self.client = pymongo.MongoClient(srv)

        db = self.client[vars[1]]
        self.coll = db[vars[2]]

        # docs to insert per batch insert
        self.bulk_size = int(vars[3])
        print("Batch size from Host:",self.bulk_size)

        # Singleton
        if (self.audit is None):
            # Log all application exceptions (and audits) to the same cluster
            self.audit = self.client.mlocust.audit

    ################################################################
    # Example helper function that is not a Locust task.
    # All Locust tasks require the @task annotation
    # You have to pass the self reference for all helper functions
    ################################################################
    def get_time(self):
        return time.time()

    ################################################################
    # Audit should only be intended for logging errors
    # Otherwise, it impacts the load on your cluster since it's
    # extra work that needs to be performed on your cluster 
    ################################################################
    def audit_err(self, type, msg):
        print("Audit: ", msg)
        self.audit.insert_one({"type":type, "ts":self.get_time(), "msg":str(msg)})

    ################################################################
    # Since the loader is designed to be single threaded with 1 user
    # There's no need to set a weight to the task.
    # Do not create additional tasks in conjunction with the loader
    # If you are testing running queries while the loader is running
    # deploy 2 clusters in mLocust with one running faker and the
    # other running query tasks
    # The reason why we don't want to do both loads and queries is
    # because of the simultaneous users and wait time between
    # requests. The bulk inserts can take longer than 1s possibly
    # which will cause the workers to fall behind.
    ################################################################
    # TODO 0 this out if doing normal load
    @task(1)
    def _bulkinsert(self):
        # Note that you don't pass in self despite the signature above
        tic = self.get_time();
        name = "bulkinsert";
 
        try:
            self.coll.insert_many([self.gen.create() for _ in range(self.bulk_size)], ordered=False)

            events.request_success.fire(request_type="pymongo", name=name, response_time=(self.get_time()-tic)*1000, response_length=0)
        except Exception as e:
            events.request_failure.fire(request_type="pymongo", name=name, response_time=(self.get_time()-tic)*1000, response_length=0, exception=e)
            self.audit_err("exception", e)
            # Add a sleep for just faker gen so we don't hammer the system with file not found ex
            time.sleep(5)
