#! /bin/bash

# usage:
#    ./test.sh [url] [start|calibrate]
#

set -x

URL=$1
ACTION=$2

[ "$URL" != "" ] || URL='http://netflowscore.appspot.com'
[ "$ACTION" != "" ] || ACTION='start'

TOKEN=`curl ${URL}/${ACTION}?version=2`
/usr/local/bin/siege --quiet -r 1 -c 20  ${URL}/test?token=${TOKEN}
SCORE=`curl ${URL}/result?token=${TOKEN}`
echo Score: ${SCORE}

