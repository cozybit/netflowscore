#! /bin/bash

# usage:
#    ./test.sh [url] [start|calibrate]
#

set -x

ACTION=$1
URL=$2

[ "$ACTION" != "" ] || ACTION='start'
[ "$URL" != "" ] || URL='http://netflowscore.appspot.com'

TOKEN=`curl ${URL}/${ACTION}?version=2`
/usr/local/bin/siege --quiet -r 1 -c 20  ${URL}/test?token=${TOKEN}
SCORE=`curl ${URL}/result?token=${TOKEN}`
echo Score: ${SCORE}

