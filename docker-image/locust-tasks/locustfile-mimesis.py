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
from bson.decimal128 import Decimal128
from decimal import Decimal
import string
from mimesis import Person
from mimesis.locales import Locale
from mimesis.enums import Gender
from mimesis import Address
from mimesis import Generic
from mimesis.schema import Field, Schema

# mimesis schema for bulk creation
# Note that increment doesn't maintain unique sequence numbers if you are running multiple mlocust users in parallel
# Not every api func has been used. The full api can be found here. https://mimesis.name/en/master/api.html
# TODO Only use what you need. The more logic you have the slower your schema generation will be.
_ = Field(locale=Locale.EN)
schema = Schema(schema=lambda: {
    "pk": _("increment"),
    "uid": _("uuid"),
    "customCode": _("random.custom_code", mask="@###", char="@", digit="#"),
    "genStr": _("random.generate_string", str_seq="abcdefg123456789", length=8),
    "randintArray": _("random.randints", amount=3, a=1, b=10000),
    "randstr": _("random.randstr", unique=False, length=10),
    "uniform": _("random.uniform", a=1.2, b=4.5, precision=10),
    "randomBytes": _("random.urandom", size=4),
    "address": {
        "addr": _("address.address"),
        "callingCode": _("address.calling_code"),
        "city": _("address.city"),
        "continent": _("address.continent"),
        "coords": _("address.coordinates"),
        "country": _("address.country"),
        "countryCd": _("address.country_code"),
        "federalSubj": _("address.federal_subject"),
        "lat": _("address.latitude"),
        "lng": _("address.longitude"),
        "postalCd": _("address.postal_code"),
        "prefecture": _("address.prefecture"),
        "province": _("address.province"),
        "region": _("address.region"),
        "state": _("address.state", abbr=False),
        "streetNm": _("address.street_name"),
        "streetNum": _("address.street_number", maximum=2999),
        "streetSuffix": _("address.street_suffix"),
        "zip": _("address.zip_code")
    },
    "finance": {
        "company": _("finance.company"),
        "companyType": _("finance.company_type", abbr=False),
        "price": _("finance.price", minimum=10, maximum=1000),
        "stockNm": _("finance.stock_name"),
        "stockTicker": _("finance.stock_ticker")
    },
    "payment": {
        "cid": _("payment.cid"),
        "cvv": _("payment.cvv"),
        "expDt": _("payment.credit_card_expiration_date", minimum=16, maximum=25),
        "ccNetwork": _("payment.credit_card_network"),
        "ccNum": _("payment.credit_card_number")
    },
    "ts": _("datetime.datetime", start=2000, end=2023),
    "formattedDt": _("datetime.formatted_date", fmt="%Y-%m-%d"),
    "month": _("datetime.month", abbr=False),
    "year": _("datetime.year", minimum=1990, maximum=2023),
    "food": {
        "dish": _("food.dish"),
        "drink": _("food.drink"),
        "fruit": _("food.fruit")
    },
    "text": {
        "alphabet": _("text.alphabet", lower_case=False),
        "answer": _("text.answer"),
        "color": _("text.color"),
        "hexColor": _("text.hex_color"),
        "level": _("text.level"),
        "quote": _("text.quote"),
        "sentence": _("text.sentence"),
        "paragraph": _("text.text", quantity=3),
        "title": _("text.title"),
        "word": _("text.word"),
        "wordArray": _("text.words", quantity=3),
    },
    "code": {
        "imei": _("code.imei"),
        "isbn": _("code.isbn"),
        "issn": _("code.issn", mask="###-##-####"),
        "pin": _("code.pin", mask="####"),
    },
    "hash": _("cryptographic.hash"),
    "bool": _("boolean"),
    "dsn": _("dsn"),
    "os": _("os"),
    "progLang": _("programming_language"),
    "version": _("version", pre_release=True),
    "timestamp": _("timestamp", posix=False),
    "numeric": {
        "int": _("numeric.integer_number", start=-1000, end=1000),
        "intArray": _("numeric.integers", start=-1000, end=1000, n=5),
        "float": _("numeric.float_number", start=-1000.0, end=1000.0, precision=7),
        "floatArray": _("numeric.floats", start=-1000.0, end=1000.0, n=5, precision=7),
    },
    "internet": {
        "content_type": _("internet.content_type"),
        "emoji": _("internet.emoji"),
        "hashtagArray": _("internet.hashtags", quantity=3),
        "hostname": _("internet.hostname"),
        "httpMethod": _("internet.http_method"),
        "httpStatusCd": _("internet.http_status_code"),
        "httpStatusMsg": _("internet.http_status_message"),
        "ipv4": _("internet.ip_v4_with_port"),
        "ipv6": _("internet.ip_v6"),
        "macAddr": _("internet.mac_address"),
        "port": _("internet.port"),
        "publicDns": _("internet.public_dns"),
        "queryParams": _("internet.query_parameters", length=3),
        "queryString": _("internet.query_string", length=3),
        "uri": _("internet.uri"),
        "url": _("internet.url"),
        "userAgent": _("internet.user_agent")
    },
    "file": {
        "nm": _("file.file_name"),
        "ext": _("file.extension"),
        "size": _("file.size", minimum=1, maximum=100)
    },
    "owner": {
        "name": _("person.name"),
        "first": _("person.first_name"),
        "last": _("person.last_name"),
        "gender": _("person.gender"),
        "nationality": _("person.nationality"),
        "title": _("person.title"),
        "occupation": _("person.occupation"),
        "lang": _("person.language"),
        "phone": _("person.telephone"),
        "height": _("person.height", minimum=1.5, maximum=2),
        "weight": _("person.weight", minimum=38, maximum=90),
        "email": _("person.email", key=str.lower),
        "username": _("person.username"),
        "password": _("person.password"),
        "token": _("token_hex"),
        "creator": _("full_name", gender=Gender.FEMALE),
    },
})

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
    client, coll, audit, bulk_size = None, None, None, None

    global schema

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

        schema.create(iterations=self.bulk_size)

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
            # self.coll.insert_many([self.gen.create() for _ in range(self.bulk_size)], ordered=False)
            self.coll.insert_many(schema*self.bulk_size, ordered=False)

            events.request_success.fire(request_type="pymongo", name=name, response_time=(self.get_time()-tic)*1000, response_length=0)
        except Exception as e:
            events.request_failure.fire(request_type="pymongo", name=name, response_time=(self.get_time()-tic)*1000, response_length=0, exception=e)
            self.audit_err("exception", e)
            # Add a sleep for just faker gen so we don't hammer the system with file not found ex
            time.sleep(5)
