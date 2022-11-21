#!/bin/bash

# script to query provenance of most recent recommendations given to a certain user
# command-line argument $1 is user_id
# output is given in json format

docker exec influxdb influx -format=json -pretty -database 'evaldb' -execute "select * from release where user_id = '$1' ORDER BY time DESC limit 5"
