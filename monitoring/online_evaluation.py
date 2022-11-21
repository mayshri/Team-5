from influxdb import InfluxDBClient
from kafka import KafkaConsumer

import pandas as pd
import numpy as np

import argparse
import requests
import time
import os

parser = argparse.ArgumentParser("Script that monitors the Kafka stream, accumulates metrics and pushes them to influxdb every n_interval seconds.")

parser.add_argument("--no_mock_data", help="Do not use mock data, but consume Kafka stream.", default=False, action="store_true")
parser.add_argument("--mock_fp", help="Filepath to load mock movielog from", default="cache/mock_movielog.txt", type=str)

parser.add_argument("--database_name", help="Name of influxdb database to write to", default="evaldb", type=str)
parser.add_argument("--database_host", help="Host of influxdb database to write to", default="influxdb", type=str)
parser.add_argument("--database_port", help="Port of influxdb database to write to", default=8086, type=int)

parser.add_argument("--seed", help="Seed for random numbers", default=42, type=int)
parser.add_argument("--n_interval", help="Interval in seconds when to push evaluation data", default=1, type=int)

parser.add_argument("--like_rating_thresh", help="Threshold for movie to be considered 'liked' - default is rating  of 3 out of 5 or higher", default=3, type=int)
parser.add_argument("--like_watchtime_thresh", help="Threshold for movie to be considered 'liked' - default is watchtime of 120 minutes or higher", default=120, type=int)


def main(database_host="influxdb", database_port=8086, database_name="evaldb", n_interval=1, **config):
    """ Consumes Kafka stream until the script is terminated. """
    
    client = InfluxDBClient(host=database_host, port=database_port, retries=5, timeout=1, database=database_name)

    consumer = get_consumer(**config)
    
    latest_recommendation = dict()
    users = dict()

    kafka_events = {
        "Recommendation": 0,
        "Watch": 0,
        "Rate": 0,
        "Malformed": 0
    }

    recommendation_status = dict()
    active_users = set()
    lags = list()

    last_push = time.time()

    print("Starting consuming stream ...")

    for msg in consumer:

        # parse kafka entry
        kind, time_dt, user_id, data = parse(msg.value)

        # save kafka event type
        kafka_events[kind] += 1

        # save lag
        if time_dt is not None:
            lags.append((pd.Timestamp.now(tz="America/Toronto") - time_dt).seconds)

        # save active user
        if user_id is not None:
            active_users.add(user_id)

        # deal with event
        if kind == "Recommendation":

            status, movie_ids = data 
            
            # query latest recommendation release
            release_info = query_release(user_id, client, **config)

            if release_info is not None:

                # save recommendation status
                if release_info["release_version"] not in recommendation_status:
                    recommendation_status[release_info["release_version"]] = {status: 1}
                elif status not in recommendation_status[release_info["release_version"]]:
                    recommendation_status[release_info["release_version"]][status] = 1
                else:
                    recommendation_status[release_info["release_version"]][status] += 1

                # reset latest recommendation for this user
                latest_recommendation[user_id] = {
                    "recommended": movie_ids,
                    "rated": dict(), 
                    "watched": dict(),
                    "release_info": (release_info["dataset_version"], release_info["release_version"], release_info["model_version"], release_info["pipeline_version"]),
                }
            
        elif kind == "Watch":

            movie_id = data

            if user_id in latest_recommendation:

                if movie_id in latest_recommendation[user_id]["watched"]:
                    latest_recommendation[user_id]["watched"][movie_id] += 1
                else:
                    latest_recommendation[user_id]["watched"][movie_id] = 1

        elif kind == "Rate":
        
            movie_id, rating = data

            if user_id in latest_recommendation:                
                latest_recommendation[user_id]["rated"][movie_id] = rating


        if time.time() > last_push + n_interval:

            now = pd.Timestamp.now()
            query_missing_users(active_users, users, **config)

            lag_points = get_lag_points(lags)
            event_points = get_event_points(kafka_events)
            user_points = get_user_points(active_users, users)
            status_points = get_status_points(recommendation_status)
            evaluation_points = get_evaluation_points(latest_recommendation, users, config)

            all_points = lag_points + event_points + user_points + status_points + evaluation_points

            for point in all_points:
                point["time"] = now

            client.write_points(all_points)

            kafka_events = {
                "Recommendation": 0,
                "Watch": 0,
                "Rate": 0,
                "Malformed": 0
            }

            recommendation_status = dict()
            active_users = set()
            lags = list()

            last_push = time.time()
            
    print("It seems that the Kafka stream has ended for some reason; shutting down ...")


def get_user_points(active_users, users):
    """ Create influxdb points from active user demographics. """
    
    points = []

    active_demographics = dict()

    for user_id in active_users:
        
        if user_id in users:

            gender, age = users[user_id]
            
            if (gender, age) in active_demographics:
                active_demographics[(gender, age)] += 1
            else:
                active_demographics[(gender, age)] = 1

    for (gender, age), n_active_users in active_demographics.items():
        points.append({
            "measurement": "active_user",
            "tags": {
                "gender": gender,
                "age": age
            },
            "fields": {
                "n_active_users": n_active_users
            }
        })

    return points
            

def get_lag_points(lags):
    """ Create influxdb points from measured lag. """

    return [{
        "measurement": "lag",
        "tags": {},
        "fields": {
            "lag": np.mean(lags)
        }
    }]


def get_evaluation_points(latest_recommendation, users, config):
    """ Create influxdb points from latest recommendations. """

    points = []

    group_buckets = {}

    for user_id, recommendation in latest_recommendation.items():

        if user_id not in users:
            continue

        gender, age = users[user_id]
        dataset_version, release_version, model_version, pipeline_version = recommendation["release_info"]

        group_tagset = (gender, age, dataset_version, release_version, model_version, pipeline_version)
        
        if group_tagset not in group_buckets:
            group_buckets[group_tagset] = [recommendation]
        else:
            group_buckets[group_tagset] += [recommendation] 

    for (gender, age, dataset_version, release_version, model_version, pipeline_version), group_recommendations in group_buckets.items():

        for k in [20, 5, 3]:

            for recommendation in group_recommendations:
                recommendation["recommended@{}".format(k)] = recommendation["recommended"][:k]

            precision, recall = evaluate(group_recommendations, k=k, **config)

            points.append({
                "measurement": "performance",
                "tags": {
                    "k": k,
                    "gender": gender,
                    "age": age,
                    "dataset_version": dataset_version,
                    "release_version": release_version,
                    "model_version": model_version,
                    "pipeline_version": pipeline_version
                },
                "fields": {
                    "precision": precision,
                    "recall": recall
                }
            })

    return points


def get_status_points(recommendation_status):
    """ Create influxdb points from recommendation status. """

    points = []

    for release_version, stati in recommendation_status.items():

        for status, n_occurrences in stati.items():
            points.append({
                "measurement": "recommendation_status",
                "tags": {
                    "release_version": release_version,
                    "status": status
                },
                "fields": {
                    "n_occurrences": n_occurrences
                }
            })

    return points



def get_event_points(kafka_events):
    """ Create influxdb points from recorded events. """

    points = []

    for event_kind, n_occurrences in kafka_events.items():

        points.append({
            "measurement": "kafka_events",
            "tags": {
                "event_kind": event_kind
            },
            "fields": {
                "n_occurrences": n_occurrences
            }
        })

    return points
                

def evaluate(recommendations, like_rating_thresh=3, like_watchtime_thresh=120, k=20, **kwargs):
    """ Evaluate a set of accumulated recommendations and the subsequent ratings and watches of the users. """

    precisions = []
    recalls = []

    for recommendation in recommendations:

        recommended_movies = set(recommendation["recommended@{}".format(k)])

        liked_rated = {movie_id for movie_id, rating in recommendation["rated"].items() if rating >= like_rating_thresh}
        liked_watched = {movie_id for movie_id, watchtime in recommendation["watched"].items() if watchtime >= like_watchtime_thresh}
        
        relevant_movies = liked_rated.union(liked_watched)

        if len(relevant_movies) > 0:

            precision = len(relevant_movies.intersection(recommended_movies)) / len(recommended_movies)
            recall = len(relevant_movies.intersection(recommended_movies)) / len(relevant_movies)

            precisions.append(precision)
            recalls.append(recall)

    if len(precisions) > 0:
        return np.mean(precisions), np.mean(recalls)
    else:
        return 0.0, 0.0


def parse(msg_str):
    """ Parse a Kafka log entry into predefined kinds and other data. """

    time_str, user_id_str, call = msg_str.split(",", maxsplit=2)

    try:
        time_dt = pd.Timestamp(time_str).tz_localize("America/Toronto")
    except:
        return "Malformed", None, None, None

    if not user_id_str.strip().isnumeric():

        return "Malformed", time_dt, None, None

    user_id = int(user_id_str.strip())

    if "recommend" in call:

        _, status_str, result = call.split(",", maxsplit=2)
    
        status = status_str.split(" ")[-1]

        if status.isnumeric():

            movie_ids = result.split(":")[-1].strip().split(", ")            

            return "Recommendation", time_dt, user_id, (status, movie_ids)

    elif "/rate/" in call:

        movie_id, rating = call.split("/")[-1].split("=")

        if rating.strip().isnumeric():

            rating = int(rating.strip())

            return "Rate", time_dt, user_id, (movie_id, rating)


    elif "/data/" in call:

        return "Watch", time_dt, user_id, call.split("/")[-2]


    return "Malformed", time_dt, user_id, None


def get_consumer(no_mock_data=False, mock_fp="cache/mock_movielog.txt", seed=42, **kwargs):
    """ Create (mock) Kafka stream consumer. """

    if no_mock_data:

            consumer = KafkaConsumer("movielog2", 
                        bootstrap_servers="fall2022-comp585.cs.mcgill.ca:9092",
                 
                 auto_offset_reset="latest",
                 value_deserializer=lambda m: m.decode("ascii"),
                 consumer_timeout_ms=60_000,
            )

    elif os.path.exists(mock_fp):
        
        class MockMsg:
            
            def __init__(self, line):

                self.value = line
    

        class MockMsgs:
            
            def __init__(self, lines):
        
                self.rng = np.random.default_rng(seed)
                self.msgs = [MockMsg(line) for line in lines]


            def __iter__(self):
    
                return self

            def __next__(self):

                return self.msgs[self.rng.integers(0, len(self.msgs), 1)[0]]


        with open(mock_fp, "r") as fh:
            consumer = MockMsgs(fh.readlines())

    else:

        raise ValueError("Mock movielog not found in {}!".format(mock_fp))

    return consumer


def query_missing_users(needed_users, users, no_mock_data=False, age_group_size=10, **kwargs):
    """ (Mock) query user API for those users for which demographic data is not yet available. """

    missing_users = needed_users - set(users.keys())

    if no_mock_data:

        for user_id in missing_users:

            try:
                resp = requests.get("http://fall2022-comp585.cs.mcgill.ca:8080/user/{}".format(user_id))
              
                user_data = resp.json()
                age_num = user_data["age"]
                gender = user_data["gender"]
            except:
                continue

            age = ">" + str((age_num // age_group_size) * age_group_size)
            users[user_id] = (gender, age)

    else:

        for user_id in missing_users:

            gender = "M" if np.random.random() > 0.5 else "F"
            age_num = np.random.randint(1, 100)

            age = ">" + str((age_num // age_group_size) * age_group_size)

            users[user_id] = (gender, age)


def query_release(user_id, client, no_mock_data=False, **kwargs):
    """ (Mock) query release data from influxdb, which should be written to by the load balancer after every recommendation. """

    if no_mock_data:

        results_set = client.query("select * from release where user_id = '{}' ORDER BY time DESC limit 1".format(user_id))
        results = list(results_set.get_points(measurement="release"))

        if len(results) > 0:
            return results[0]
        else:
            return None

    else:

        result = {
            "dataset_version": "test", 
            "release_version": "0.0.1", 
            "model_version": "test1",
            "pipeline_version": "test"
        }

        if np.random.random() > 0.9:
            result["release_version"] = "0.0.2"

        if np.random.random() > 0.3:
            result["model_version"] = "test2"

    return result


if __name__ == "__main__":
    args = parser.parse_args()
    main(**vars(args))