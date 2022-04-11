import pymongo
from bson.json_util import loads, dumps
from bson import json_util
import csv
import sys
import uuid
import os
import itertools
from faker import Faker
from collections import defaultdict
import json
import datetime
from deepmerge import Merger
import random
import re

############################################################################################################
# This is a utility that takes in the model name. The model file name has a suffix that indicates
# how many records should be added to the list before returning the results. 
# The objective is to send back the largest list possible without killing the mLocust
# worker CPU/RAM
############################################################################################################

# This used to uppercase the first letter of the string. Removed it for now.
stripProp = lambda str: re.sub(r'\s+', '', (str[0] + str[1:].strip('()')))
fake = Faker()

# This serializer isn't needed anymore as long as we use faker.datetime.datetime instead of datetime.date
# I'll keep this serializer code in here in case someone in the future needs to use it for another data type that isn't native...
def ser(o):
    """Customize serialization of types that are not JSON native"""
    if isinstance(o, datetime.date):
        return str(o)

def procpath(path, counts, generator):
    """Recursively walk a path, generating a partial tree with just this path's random contents"""
    stripped = stripProp(path[0])
    if len(path) == 1:
        # Base case. Generate a random value by running the Python expression in the text file
        return { stripped: eval(generator) }
    elif path[0].endswith('()'):
        # Lists are slightly more complex. We generate a list of the length specified in the
        # counts map. Note that what we pass recursively is _the exact same path_, but we strip
        # off the ()s, which will cause us to hit the `else` block below on recursion.
        return {
            stripped: [ procpath([ path[0].strip('()') ] + path[1:], counts, generator)[stripped] for X in range(0, counts[stripped]) ]
        }
    else:
        # Return an object, of the specified type, populated recursively.
        return {
            # stripped: {
            stripped: procpath(path[1:], counts, generator)
            # }
        }

def zipmerge(the_merger, path, base, nxt):
    """Strategy for deepmerge that will zip merge two lists. Assumes lists of equal length."""
    return [ the_merger.merge(base[i], nxt[i]) for i in range(0, len(base)) ]

def ID(key):
    id_map[key] += 1
    return key + str(id_map[key]+starting_id_minus_1)

# A deep merger using our custom list merge strategy.
merger = Merger([
    (dict, "merge"),
    (list, zipmerge)
], [ "override" ], [ "override" ])

# This field is used for an incremental field, e.g. ID. We can't really control this using mLocust so we'll always default to 0. 
# Not every loader file may require this.
starting_id_minus_1 = 0 
id_map = defaultdict(int)

# Set a variable for how many array elements someone wants
maxArraySize = 5
def setArraySize(size):
     global maxArraySize
     maxArraySize = size
     return size

def bulkFetch(model, bulk_size):
    template = "models/" + model 
    # Need to check if the model exists because the GKE container runs in a higher directory
    if not os.path.isfile(template): 
        template = "locust-tasks/" + template
    # final check to see if the template exists
    if not os.path.isfile(template):
        raise Exception("Model file not found. " + template)

    # instantiate a new list
    l = []

    for J in range(0, bulk_size): # iterate through the bulk insert count
        # A dictionary that will provide consistent, random list lengths
        counts = defaultdict(lambda: random.randint(1, maxArraySize))
        data = {}
        with open(template) as csvfile:
            propreader = csv.reader(itertools.islice(csvfile, 1, None))
            for row in propreader:
                path = row[0].split('.')
                # print(path)
                partial = procpath(path, counts, row[3])
                # print(partial);
                # Merge partial trees.
                data = merger.merge(data, partial)
                # print(data);
        # print(data);

        # To JSON!
        # Old debugging statements that used the custom deserializer. Non-issue if you use native bson/json data types
        # print("%s\t%s\t%s"%(str(id), str(idempotencyKey), json.dumps(obj, default=ser)))
        # print(json.dumps(obj, default=ser))

        # Add the object to our list
        l.append(data)

    return l
