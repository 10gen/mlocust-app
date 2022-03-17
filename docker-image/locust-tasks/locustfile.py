#!/usr/bin/env python

########################################################################
#
# Many of you like to get fancy by creating separate object classes
# and external file dependencies, e.g. json files, 
# I discourage you from doing that because there are file path
# reference issues that make things difficult when you containerize
# and deploy to gke. Try to keep everything in this 1 file.
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

########################################################################
# Global Static Variables that can be accessed without referencing self
# Change the connection string to point to the correct db 
# and double check the readpreference etc.
########################################################################
try:
    client = pymongo.MongoClient("mongodb+srv://<username>:<password>@<srv>/myFirstDatabase?retryWrites=true&w=majority&readPreference=secondaryPreferred")
    coll = client.sample_airbnb.listingsAndReviews
    # Log all application exceptions (and audits) to the same cluster
    audit = client.locust.audit
except Exception as e:
   print('Fatal Exception (unable to log error): ', e)
   exit()

class MetricsLocust(User):
    ####################################################################
    # All performance POVs measure based on requests/sec (RPS).
    # Throttle all tasks per user to run every second.
    # Do not touch this parameter.
    # If we don't throttle, then each user will run as fast as possible,
    # and will kill the CPU of the machine.
    # We can increase throughput by running more concurrent users.
    ####################################################################
    wait_time = between(1, 1)

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
    def audit(self, type, msg):
        print("Audit: ", msg)
        audit.insert_one({"type":type, "ts":self.get_time(), "msg":str(msg)})

    ################################################################
    # Start defining tasks and assign a weight to it.
    # All tasks need the @task() notation.
    # Weights indicate the chance to execute, e.g. 1=1x, 5=5x, etc.
    ################################################################
    @task(1)
    def _async_find(self):
        # Note that you don't pass in self despite the signature above
        tic = self.get_time();
        name = "singleFetch";

        try:
            # Get the record from the TEST collection now
            coll.find_one({}, {"_id":1})
            events.request_success.fire(request_type="pymongo", name=name, response_time=(time.time()-tic), response_length=0)
        except Exception as e:
            events.request_failure.fire(request_type="pymongo", name=name, response_time=(time.time()-tic), response_length=0, exception=e)
            self.audit("exception", e)
