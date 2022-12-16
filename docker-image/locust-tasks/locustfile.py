#!/usr/bin/env python

########################################################################
#
#                    Recommended Usage:
#                    Users: 1000 * workers
#                    Host: srv|db|coll
#
########################################################################

########################################################################
#
# ANYTHING THAT REQUIRES YOUR ATTENTION WILL HAVE A TODO IN THE COMMENTS
# Do not create external files outside of this locust file!
# mLocust only allows you to upload a single python file atm.
# Please keep everything in this 1 file.
#
########################################################################

# Allows us to make many pymongo requests in parallel to overcome the single threaded problem
import gevent
_ = gevent.monkey.patch_all()

########################################################################
# TODO Add any additional imports here.
# TODO Make sure to include in requirements.txt if necessary
########################################################################
import pymongo
from bson import json_util
from bson.json_util import loads
from bson import ObjectId
from locust import User, events, task, constant, tag, between
import time

class MetricsLocust(User):

    ########################################################################
    # Class variables. The values are initialized with None
    # till they get set from the actual locust exeuction 
    # when the host param is passed in.
    # DO NOT MODIFY! PASS IN VIA HOST PARAM.
    ########################################################################
    client, coll, audit = None, None, None

    ####################################################################
    # You can throttle tasks being executed by each simulated user
    # Only do this if the client really wants to simulate n-number
    # of users. Otherwise, if you leave this commented out,
    # the performance will increase by 400%
    ####################################################################
    # wait_time = between(1, 1)

    ####################################################################
    # Initialize any env vars from the host parameter
    # Set the target collections and such here
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

        # Singleton
        if (self.audit is None):
            # Log all application exceptions (and audits) to the same cluster
            self.audit = self.client.mlocust.audit

    ################################################################
    # Example helper function that is not a Locust task.
    # All Locust tasks require the @task annotation
    # You have to pass the self reference for all helper functions
    # TODO Create any additional helper functions here
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
    # Start defining tasks and assign a weight to it.
    # All tasks need the @task() notation.
    # Weights indicate the chance to execute, e.g. 1=1x, 5=5x, etc.
    # TODO Create any additional task functions here
    ################################################################
    @task(1)
    def _async_find(self):
        # Note that you don't pass in self despite the signature above
        tic = self.get_time();
        name = "singleFetch";

        try:
            # Get the record from the target collection now
            self.coll.find_one({}, {"_id":1})
            events.request_success.fire(request_type="pymongo", name=name, response_time=(self.get_time()-tic)*1000, response_length=0)
        except Exception as e:
            events.request_failure.fire(request_type="pymongo", name=name, response_time=(self.get_time()-tic)*1000, response_length=0, exception=e)
            self.audit_err("exception", e)