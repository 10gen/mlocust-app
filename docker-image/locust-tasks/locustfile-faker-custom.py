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
import pprint

from bson.codec_options import TypeRegistry, CodecOptions, TypeCodec
from bson.decimal128 import Decimal128
from decimal import Decimal
import string

########################################################################
# Global Static Variables that can be accessed without referencing self
# Change the connection string to point to the correct db 
# and double check the readpreference etc.
########################################################################
client = None
coll = None
# Log all application exceptions (and audits) to the same cluster
audit = None
# docs to insert per batch insert
batch_size = None 

fake = Faker()

# Custom Class
class SampleProduct:

    def create_product(self):
        return {
            "testName": fake.name(),
            "orderNumber": fake.bothify(text = "AD-#########"),
            # "orderStatus": random.choice(["open", "shipped", "declined", "unpaid", "returned"]),
            "orderID": fake.uuid4(),
            "shard": random.randint(1,25000),
            "orderStatus": "open",
            "channel": self.get_channel(),
            "orderReference": fake.bothify(text = "????????????", letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'),
            "brand": self.get_brand(),
            "orderType": self.get_order_type(),
            "orderDate": fake.date_time_between(start_date=datetime(2017, 12, 31)),
            "currency": self.get_currency(),
            "locale": "en_US",
            "integrator": "storefront",
            "invoiceNumber": fake.bothify(text = "########"),
            "orderTaxes": self.get_order_taxes(),
            "orderLines": self.get_order_lines(),
            "payments": self.get_payments(),
            "promotions": self.get_promotions(),
            "orderCharges": self.get_order_charges(),
            "shipments": self.get_shipments(),
            "customer": self.get_customer(),
            "references": self.get_references(),
            "notes": self.get_notes()
        }

    def get_channel(self):
        return random.choice(["Web", "App", "Brick", "Marketplace"])

    def get_brand(self):
        return random.choice(["adadas", "nikey", "reebock", "old balance", "asick"])

    def get_order_type(self):
        return random.choice(["SALES", "SALES", "SALES", "PROMO", "COUPON"])

    def get_currency(self):
        return random.choice(["USD", "EUR", "CNY", "USD", "EUR"])

    def get_order_lines(self):
        order_lines = []
        for i in range(1, self.order_item_quantity):
            order_lines.append({
                "lineNumber": 1,
                "SKU": fake.bothify(text = "??????????", letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'),
                "productLiteralSize": round(random.uniform(2,13), 1),
                "productName": fake.color_name() + ' Shirt',
                "productImage": "https://edge.disstg.commercecloud.salesforce.com/dw/image/v2/aaqx_stg/on/demandware.static/Sites-adidas-US-Site/Sites-adidas-products/en_US/v1643728798340/zoom/034563_01_standard.jpg",
                "UPC": random.randint(100000000000,900000000000),
                "divisionCode": random.randrange(1,9),
                "orderedQuantity": self.order_item_quantity,
                "unitGrossPrice": round(random.uniform(1,220), 2),
                "unitNetPrice": round(random.uniform(1,250), 2),
                "orderLineCharges": [
                    {
                    "chargeName": random.choice(["OUTLET_MARKDOWN-ALL", "COUPON", "NONE"]),
                    "chargeAmount": round(random.uniform(1,25), 2)
                    }
                ],
                "orderLineTaxes": [
                    {
                    "taxName": "ShippingTax",
                    "taxAmount": round(random.uniform(1,5), 1),
                    "taxClass": fake.bothify(text = "????????", letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'),
                    "taxRate": round(random.uniform(1,7), 2),
                    }
                ],
                "vasCode": "string",
                "giftArticle": False,
                "shippingGroup": "00149542",
                "lineType": "inline",
                "references": self.get_references()
            })
        return order_lines

    def get_references(self):
        a = []
        for i in random.randint(15,25):
            a.append({
                random.choice(["EAN","UPC","aromaStatus","articleNumber","campaignID","color","division","flashProduct","gender","image","literalSize","literalSizeID","modelNumber","promotionId","promotionName","proratedGrossBaseDiscount","proratedGrossDiscount","proratedNetBaseDiscount","proratedNetDiscount","proratedTaxDiscount","returnType","size","sourceInfo","taxClassID","type"]): fake.bothify(text = "??????", letters = 'abcdefghijklmnopqrstuvwxyz1234567890')
            })

    def get_payments(self):
        return [
                {
                    "requestedAmount": round(random.uniform(1,160), 2),
                    "paymentGateway": random.choice(["ACI", "SIX", "ONE"]),
                    "paymentMethod": random.choice(["CREDIT_CARD", "CREDIT_CARD", "CREDIT_CARD", "CASH", "COUPON"]),
                    "collectedFromConsumer": random.randint(1,9),
                    "creditCardNo": random.randint(1000000000000000,9000000000000000),
                    "creditCardExpDate": random.randint(100000,900000),
                    "pspReference": random.choice(string.ascii_letters),
                    "reference": [
                        {
                            "name": "patchInfo",
                            "value": fake.bothify(text = "????????????????????????????????????????????????????????????", letters = 'abcdefghijklmnopqrstuvwxyz1234567890'),
                        },
                        {
                            "name": "authCode",
                            "value": random.randint(100000000000,900000000000)
                        },
                        {
                            "name": "authResult",
                            "value": "AUTHORISED"
                        },
                        {
                            "name": "pspReference",
                            "value": fake.bothify(text = "????????????????", letters = 'abcdefghijklmnopqrstuvwxyz1234567890'),
                        }
                    ]
                }
            ]

    def get_promotions(self):
        return [
                {
                "promotionType": "voucher",
                "promotionId": random.randint(100000000000,900000000000),
                "promotionName": "sale",
                "campaignId": random.randint(100000000000,900000000000)
                }
            ]

    def get_shipments(self):
        return [
                {
                "shipmentId": random.randint(10000000,90000000),
                "carrierName":  random.choice(["Standard Delivery", "Express Delivery", "One-day Delivery"]),
                "carrierCode": random.choice(["GRND", "AIR"]),
                "shipmentType": "inline",
                "shippingMethod": "Standard-FED-Unregistered",
                "shippingAddress": {
                    "firstName": fake.first_name(),
                    "lastName": fake.last_name(),
                    "addressLine1": fake.street_name(),
                    "addressLine2": "Unit A",
                    "city": fake.city(),
                    "state": "Taxas",
                    "postalCode": fake.postcode(),
                    "country": fake.country()
                },
                "pickupPointId": random.randint(10000000,99999999),
                "references": [
                    {
                        "name": "carrierCode",
                        "value": random.choice(["GRND", "AIR"])
                    },
                    {
                        "name": "carrierServiceCode",
                        "value": random.randint(100000000000,999999999999)
                    },
                    {
                        "name": "collectionPeriod",
                        "value": fake.date_time_between(start_date=datetime(2020, 12, 31)),
                    },
                    {
                        "name": "deliveryPeriod",
                        "value": fake.date_time_between(start_date=datetime(2020, 12, 31)),
                    },
                    {
                        "name": "type",
                        "value": "inline"
                    }
                ]
                }
            ]

    def get_customer(self):
        return {
                "customerContactID": random.randrange(1,8),
                "customerId": fake.bothify(text = "????????????", letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'),
                "customerEmail": fake.ascii_email(),
                "customerPhone": fake.phone_number(),
                "customerBillingAddress": {
                    "addressLine1": fake.street_address(),
                    "city": fake.city(),
                    "state": fake.current_country(),
                    "postalCode": fake.postcode(),
                    "country": fake.country()
                }
            }

    def get_references(self):
        return [
                {
                    "name": "BICExportStatus",
                    "value": random.randrange(1,5)
                },
                {
                    "name": "CartId",
                    "value": fake.bothify(text = "????????????????????", letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890')
                },
                {
                    "name": "ChannelNo",
                    "value": "web"
                },
                {
                    "name": "ExactTargetExportStatus",
                    "value": random.randrange(1,5)
                },
                {
                    "name": "userAgent",
                    "value": fake.user_agent()
                },
                {
                    "name": "NPSSurveyAttributes",
                    "value": "&amp;g1=M&amp;c1=Shoes&amp;t1=Socce"
                },
                {
                    "name": "environment",
                    "value": "development-test-adidasgroup-eu.demandware.net"
                },
                {
                    "name": "paymentMethod",
                    "value": "CREDIT_CARD"
                }
            ]

    def get_notes(self):
        return [
                {
                    "created-by": "storefront",
                    "creation-date": fake.date_time_between(start_date=datetime(2020, 1, 1)),
                    "subject": "AvalaraDocCode",
                    "text": fake.bothify(text = "????????????????????", letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
                },
                {
                    "created-by": "storefront",
                    "creation-date": fake.date_time_between(start_date=datetime(2020, 12, 31)),
                    "subject": "AvalaraDocCode",
                    "text": fake.bothify(text = "????????????????????", letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
                },
                {
                    "created-by": "storefront",
                    "creation-date": fake.date_time_between(start_date=datetime(2020, 12, 31)),
                    "subject": "CartId",
                    "text": fake.bothify(text = "????????????????????", letters = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
                },
                {
                    "created-by": "storefront",
                    "creation-date": fake.date_time_between(start_date=datetime(2020, 12, 31)),
                    "subject": "AciPaymentHelper-validateHostedPaymentAuthorizationResult",
                    "text": "AciPaymentLib:validateHostedPaymentAuthorizationResult() - AuthCode = 000.100.112, AuthResult = AUTHORISED, Description = Request successfully processed in 'Merchant in Connector Test Mode', id = 8ac7a4a07eb7f657017eb8f6cd772001, ndc = 552BEDE2B4FDB62F6C6ABAC3BBD3C618.uat01-vm-tx03. Order was placed, order status was updated from Created to New."
                },
                {
                    "created-by": "storefront",
                    "creation-date": fake.date_time_between(start_date=datetime(2020, 12, 31)),
                    "subject": "AciPaymentHelper-validateHostedPaymentAuthorizationResult",
                    "text": "AciPaymentLib:validateHostedPaymentAuthorizationResult() - AuthCode = 000.100.112, AuthResult = AUTHORISED, Description = Request successfully processed in 'Merchant in Connector Test Mode', id = 8ac7a4a07eb7f657017eb8f6cd772001, ndc = 552BEDE2B4FDB62F6C6ABAC3BBD3C618.uat01-vm-tx03. Order total is captured"
                }
            ]

    def get_order_taxes(self):
        return [
                {
                    "taxName": "ShippingTax",
                    "taxAmount": round(random.uniform(1,5), 2),
                    "taxClass": "FullTax",
                    "taxRate": round(random.uniform(1,8), 2)
                }
            ]

    def get_order_charges(self):
        return [
                {
                    "chargeName": "OrderLineTax",
                    "chargeAmount": round(random.uniform(1,7), 2)
                }
            ]

# Init this after class declaration above
generator = SampleProduct()

########################################################################
# Even though locust is designed for concurrency of simulated users,
# given how resource intensive fakers/bulk inserts are,
# you should only run 1 simulated user / worker else you'll kill the 
# CPU of the workers.
########################################################################
class MetricsLocust(User):
    ####################################################################
    # Unlike a standard locust file where we throttle requests on a per
    # second basis, since we are trying to load data asap, there will 
    # be no throttling
    ####################################################################

    def __init__(self, parent):
        super().__init__(parent)

        global client, coll, audit, batch_size

        # Singleton
        if (client is None):
            # Parse out env variables from the host
            vars = self.host.split("|")
            srv = vars[0]
            print("SRV:",srv)
            client = pymongo.MongoClient(srv)

            db = client[vars[1]]
            coll = db[vars[2]]

            # docs to insert per batch insert
            batch_size = int(vars[3])
            print("Batch size from Host:",batch_size)

            # Log all application exceptions (and audits) to the same cluster
            audit = client.mlocust.audit

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

    # TODO Set this to 0 so bulkinsert goes as fast as possible. Make sure to simulate 1 user per worker only.
    wait_time = between(0, 0)

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
 
        global coll, audit

        try:
            coll.insert_many([generator.create_product() for _ in range(batch_size)], ordered=False)

            events.request_success.fire(request_type="pymongo", name=name, response_time=(time.time()-tic)*1000, response_length=0)
        except Exception as e:
            events.request_failure.fire(request_type="pymongo", name=name, response_time=(time.time()-tic)*1000, response_length=0, exception=e)
            self.audit("exception", e)
            # Add a sleep for just faker gen so we don't hammer the system with file not found ex
            time.sleep(5)

