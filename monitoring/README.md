# Monitoring & Online Evaluation

Separate tool that monitors [Kafka stream](https://kafka.apache.org/documentation/streams/), accumulates metrics, and periodically pushes them to [InfluxDB](https://www.influxdata.com/), where they are visualized via [Grafana](https://grafana.com/). Requires [Docker](https://www.docker.com/) and access to Kafka stream and user API when not run with mock data.

The main code is the Python script [online_evaluation.py](online_evaluation.py), which consumes the Kafka stream, reads release data from InfluxDB, queries user demographics, and pushes data to InfluxDB.

## Set Up Monitoring Infrastructure

To start the monitoring infrastructure, run `bash host.sh`, which will create the necessary docker containers (and delete them if they were previously running). Release-related visualizations will only be available if the recommender system runs as well in the docker network `evalnet` and push release information to the  InfluxDB database `evaldb` for each recommendation.

When running locally, comment out the command-line argument `--no_mock_data` in the [Dockerfile](Dockerfile). On the VM, comment it in in order to use real data instead of mock data.

Grafana will be hosted at `localhost:3000`. When running on the VM, it is recommended to map this port on the VM with an SSH tunnel to a local port, e.g. to `localhost:8082` via:

```ssh team-5@fall2022-comp585-5.cs.mcgill.ca -N -f -L 8082:127.0.0.1:3000```

Grafana should then be available at [http://127.0.0.1:8082](http://127.0.0.1:8082).

In order to export the current state of the Grafana dashboard to a `dashboard.json`, run `export_dashboard.sh`. It will then be restored the next time `host.sh` is run.

## Qury InfluxDB for Provenance

InfluxDB can be used to determine the `release`, `model`, `data`, and `pipeline` versions with which a certain recommendation was made. The provenance of all recommendations is stored in the `release` measurement in the InfluxDB database `evaldb`. 

To query for example the origins of the five most recent recommendation for a user `$USER_ID`, run `bash check_provenance.sh $USER_ID`. To learn the provenance of a recommendation that was earlier, either increase the limit in `check_provenance.sh` or formulate another query based on time or other idenfitiers using [InfluxQL](https://docs.influxdata.com/influxdb/v1.8/query_language/).

For more complex queries, the interactive mode of InfluxDB might be more suitable:

```docker exec -it influxdb influx -database 'evaldb' -precision rfc3339 -format=json -pretty```

A query that retrieves the provenance of a recommendation whose exact time and user was known could look e.g. like this:

``` SELECT * FROM release WHERE user_id = '$USER_ID' AND time = '$TIME' limit 1 ```

where `$TIME` is a RFC3339 timestamp such as `2021-12-07T02:53:50.799907Z` and `$USER_ID` is an int such as `2`.
