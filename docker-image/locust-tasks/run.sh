#!/bin/bash

# Copyright 2015 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

LOCUST="/usr/local/bin/locust"
LOCUS_OPTS="-f /locust-tasks/locustfile.py --host=$LOCUST_HOST"
LOCUST_MODE=${LOCUST_MODE:-standalone}

# Extra logic to grab an external locust file
# This will go into mLocust 2.0 when we have a base img and just dynamically fetch a new locust file.
#if [[ ! -z $LOCUST_FILE_PATH ]]; then
#    wget $LOCUST_FILE_PATH -O /locust-tasks/locustfile.py 
#fi

if [[ ! -z $LOCUST_REQTS_PATH ]]; then
    wget $LOCUST_REQTS_PATH -O /locust-tasks/requirements.txt
fi

# We may need to run python -m pip install --upgrade pip to get past the gevent wheel building issue...
# Install the required dependencies via pip
pip install -r /locust-tasks/requirements.txt

if [[ "$LOCUST_MODE" = "master" ]]; then
    LOCUS_OPTS="$LOCUS_OPTS --master"
elif [[ "$LOCUST_MODE" = "worker" ]]; then
    LOCUS_OPTS="$LOCUS_OPTS --worker --master-host=$LOCUST_MASTER"
fi

echo "$LOCUST $LOCUS_OPTS"

$LOCUST $LOCUS_OPTS
