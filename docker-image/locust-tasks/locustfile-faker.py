#!/usr/bin/env python

########################################################################
#
#                    Recommended Usage:
#                    Users: 1 * workers
#                    Host: srv|db|coll|model|bulksize
#
########################################################################

########################################################################
#
# ANYTHING THAT REQUIRES YOUR ATTENTION WILL HAVE A TODO IN THE COMMENTS
# Do not create external files outside of this locust file!
# mLocust only allows you to upload a single python file atm.
# Please keep everything in this 1 file.
# The only exception to this rule are faker models which need to be
# pre-built and tested and checked in.
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
import fakerutil

########################################################################
# Global Static Variables that can be accessed without referencing self
# The values are initialized with None till they get set from the
# actual locust exeuction when the host param is passed in.
########################################################################
# DO NOT MODIFY! PASS IN VIA HOST PARAM.
client = None
coll = None
audit = None
# TODO If you are using a custom model, make sure it gets checked in
model = None 
bulk_size = None

########################################################################
# Even though locust is designed for concurrency of simulated users,
# given how resource intensive fakers/bulk inserts are,
# you should only run 1 simulated user / worker else you'll kill the 
# CPU of the workers.
# TODO In the locust UI, specify 1 user per worker
########################################################################
class MetricsLocust(User):
    ####################################################################
    # Unlike a standard locust file where we throttle requests on a per
    # second basis, since we are trying to load data asap, there will 
    # be no throttling
    ####################################################################

    ####################################################################
    # Initialize any env vars from the host parameter
    # Make sure it's a singleton so we only set conn pool once
    # Set the target collections and such here
    ####################################################################
    def __init__(self, parent):
        super().__init__(parent)

        # specify that the following vars are global vars
        global client, coll, audit, model, bulk_size

        # Singleton
        # TODO Pass in the env vars using the Host field for locust, e.g. srv|db|coll|model|bulkSize
        # TODO Make sure your srv has the right read and write preference to optimize perf
        if (client is None):
            # Parse out env variables from the host
            # FYI, you can pass in more env vars if you so choose
            vars = self.host.split("|")
            srv = vars[0]
            print("SRV:",srv)
            client = pymongo.MongoClient(srv)

            # Define the target db and coll here
            db = client[vars[1]]
            coll = db[vars[2]]

            # Specify the model, without the model directory name.
            # The model must be checked into git else it wont' work in prod
            model = vars[3]

            bulk_size = int(vars[4])

            # Log all application exceptions (and audits) to the same cluster
            audit = client.mlocust.audit

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
    def audit(self, type, msg):
        print("Audit: ", msg)
        audit.insert_one({"type":type, "ts":self.get_time(), "msg":str(msg)})

    ################################################################
    # Since the loader is designed for 1 user
    # There's no need to set a weight to the task.
    # Do not create additional aggregation/find tasks in conjunction with the loader
    # If you are testing running queries while the loader is running
    # deploy 2 clusters in mLocust with one running faker and the
    # other running query tasks
    # The reason why we don't want to do both loads and queries is
    # because of the simultaneous users and wait time between
    # requests. The bulk inserts can take longer than 1s possibly
    # which will cause the workers to fall behind.
    ################################################################
    @task(1)
    def _bulkinsert(self):
        # Note that you don't pass in self despite the signature above
        tic = self.get_time();
        name = "bulkinsert";

        try:
            # Logic for bulk insert goes here using the pyfaker util
            l = fakerutil.bulkFetch(model, bulk_size)
            coll.insert_many(l)

            events.request_success.fire(request_type="pymongo", name=name, response_time=(time.time()-tic)*1000, response_length=0)
        except Exception as e:
            events.request_failure.fire(request_type="pymongo", name=name, response_time=(time.time()-tic)*1000, response_length=0, exception=e)
            self.audit("exception", e)
            # Add a sleep for just faker gen so we don't hammer the system with file not found ex
            time.sleep(5)
