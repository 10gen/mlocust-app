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
wget -O /locust-tasks/locustfile.py https://stitch-statichosting-prod.s3.amazonaws.com/61a645aaa483c35ff9955c28/locustfile.py?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAZ5A3K6VY7LDWGOX4%2F20221222%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20221222T211544Z&X-Amz-Expires=60&X-Amz-SignedHeaders=host&X-Amz-Signature=29b524ffce4876b16a8065fdcd201d0c4ddb09536a37f6412f35a3a66886e393

if [[ "$LOCUST_MODE" = "master" ]]; then
    LOCUS_OPTS="$LOCUS_OPTS --master"
elif [[ "$LOCUST_MODE" = "worker" ]]; then
    LOCUS_OPTS="$LOCUS_OPTS --worker --master-host=$LOCUST_MASTER"
fi

echo "$LOCUST $LOCUS_OPTS"

$LOCUST $LOCUS_OPTS
