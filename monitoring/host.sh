#!/bin/bash

echo "Killing old docker items ..."

docker network create evalnet &>/dev/null
docker network disconnect evalnet grafana &>/dev/null
docker network disconnect evalnet influxdb &>/dev/null
docker network disconnect evalnet online-evaluation &>/dev/null

docker container kill grafana &>/dev/null
docker container kill influxdb &>/dev/null
docker container kill online-evaluation &>/dev/null

docker volume rm grafana &>/dev/null
docker volume rm influxdb &>/dev/null

docker container rm online-evaluation &>/dev/null
docker image rm online-evaluation:latest &>/dev/null
sleep 1

echo "Running influxdb ..."
docker run --rm -d -p 8086:8086 -v influxdb:/var/lib/influxdb --env INFLUXDB_DATA_MAX_VALUES_PER_TAG=0 --name influxdb influxdb:1.8
sleep 1

echo "Creating influxdb database evaldb ..."
docker exec influxdb influx -execute 'drop database evaldb'
docker exec influxdb influx -execute 'create database evaldb'
sleep 1

echo "Connecting influxdb to evalnet ..."
docker network connect evalnet influxdb
sleep 1

echo "Building online evaluation ..."
docker build . -t online-evaluation:latest &>/dev/null
sleep 1

echo "Running online evaluation in evalnet ..."
docker run -d --network evalnet --name online-evaluation online-evaluation:latest
sleep 1

echo "Running Grafana ..."
docker run --rm -d -p 3000:3000 -v grafana:/var/lib/grafana --env GF_SECURITY_ADMIN_PASSWORD="team5" --env GF_SECURITY_ADMIN_USER="team5" --name grafana grafana/grafana
sleep 1

echo "Connecting Grafana to evalnet ..."
docker network connect evalnet grafana

echo "Waiting 60 seconds for Grafana to start up before requesting API key ..."
sleep 60

echo "Importing Grafana datasources and dashboards ..."
apikeyjson=$(curl -s -X POST -H "Content-Type: application/json" -d '{"name":"apikeycurl", "role": "Admin"}' http://team5:team5@localhost:3000/api/auth/keys)
sleep 1

echo "API Key JSON: $apikeyjson"
apikey=$(python3 -c "import json; print(json.loads('$apikeyjson')['key'])")
sleep 1

echo "API Key: $apikey"
echo "$apikey" > apikey.txt
curl -s -X POST --insecure -H "Authorization: Bearer $apikey" -H "Content-Type: application/json" -d @datasource.json http://localhost:3000/api/datasources >/dev/null
curl -s -X POST --insecure -H "Authorization: Bearer $apikey" -H "Content-Type: application/json" -d @dashboard.json http://localhost:3000/api/dashboards/db >/dev/null

echo "Grafana is now available at http://localhost:3000."