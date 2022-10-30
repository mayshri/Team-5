import json
import time
from collections import defaultdict

import requests
from kafka import KafkaConsumer

from src import config
from src.process import check_movie_id, check_timestamp, check_user_id


def multi_dict(n, type):
    if n == 1:
        return defaultdict(type)
    else:
        return defaultdict(lambda: multi_dict(n - 1, type))


class OnlineEvaluation:
    def __init__(self, timeinterval, online_evaluation_threshold, save=True):

        self.timeinterval = timeinterval
        self.timestamp = int(time.time())
        self.online_evaluation_threshold = online_evaluation_threshold
        self.savedata = save

        self.recommendations = {}
        self.movie_watched_length = multi_dict(3, str)

        self.num_of_recommendations = 0
        self.recommended_watch_num = 0
        self.total_watch_num = 0

        self.recommended_watch_time = 0
        self.recommended_movie_length = 0

        self.recommended_movies_positive_rating = 0
        self.total_recommendations_rated = 0

        self.recommended_rank_sum = 0

        self.setup_online_testing()

    def parse_entry(self, entry):
        parsed = entry.value.decode().split(",")

        timestamp = parsed[0]
        user_id = parsed[1]
        if check_user_id(user_id) is False:
            return

        # If length is <= 3 then the request is either a /data/ or /rate/ request

        if len(parsed) <= 3:

            if check_timestamp(timestamp) is False:
                return
            user_recommendations = self.recommendations.get(
                user_id
            )  # Get all recommendations for this user
            # If the user has no recommendations, then we return as we don't make use of this data

            if user_recommendations is None:
                return

            # If it is a /data/ request, we want to compute the "Recommended Movie Watch Rate" &
            # "Average watch time proportion" & "Average watched movie rank"
            if parsed[2].find("/data/") != -1:
                movie_id = parsed[2].split("/")[3]

                if not check_movie_id(movie_id):
                    return

                movie_info = requests.get(
                    "http://fall2022-comp585.cs.mcgill.ca:8080/movie/" + movie_id
                ).json()
                if "runtime" not in movie_info:
                    return
                movie_length = int(movie_info["runtime"])
                if movie_length == 0:
                    return

                if self.movie_watched_length[user_id].get(movie_id) is None:
                    if movie_id in user_recommendations:
                        self.recommended_watch_num += 1
                        self.recommended_rank_sum += (
                            user_recommendations.index(movie_id) + 1
                        )
                        self.recommended_watch_time += 1
                        self.recommended_movie_length += movie_length
                    self.movie_watched_length[user_id][movie_id] = 1
                    self.total_watch_num += 1
                else:
                    if movie_id in user_recommendations:
                        self.recommended_watch_time += 1
                    self.movie_watched_length[user_id][movie_id] += 1
                self.print_temp_metrics(self.timestamp)
                return

            # If it is a /rate/ request, we want to compute the "Recommendation Accuracy" Rate
            elif parsed[2].find("/rate/") != -1:
                movie_rating = parsed[2].split("/rate/")[1]

                rating = movie_rating.split("=")[1]
                movie_id = movie_rating.split("=")[0]

                if not check_movie_id(movie_id):
                    return

                if movie_id in user_recommendations:
                    self.total_recommendations_rated += 1
                    if float(rating) >= 4:
                        self.recommended_movies_positive_rating += 1
                self.print_temp_metrics(self.timestamp)
                return
            else:
                return

        if parsed[2].find("recommendation request") != -1:
            if self.num_of_recommendations >= self.online_evaluation_threshold:
                return
            # Parse the movies so we only get the movies id
            movies_recommended = parsed[4:24]
            movies_recommended[0] = movies_recommended[0].replace("result: ", "")
            movies_recommended = [s.strip() for s in movies_recommended]
            self.recommendations[user_id] = movies_recommended
            self.num_of_recommendations += 1
        return

    def write_metrics(self, timestamp):
        # Write the metrics to a file
        with open(config.RECOMMENDEDMOVIEWATCHRATE, "a") as f:
            print("writing watch rate", str(self.compute_recommendation_watch_rate()))
            f.write(
                str(timestamp)
                + " "
                + str(self.compute_recommendation_watch_rate())
                + "\n"
            )
        with open(config.RECOMMENDEDMOVIEACCURACY, "a") as f:
            print("writing accuracy", str(self.compute_recommendation_accuracy()))
            f.write(
                str(timestamp)
                + " "
                + str(self.compute_recommendation_accuracy())
                + "\n"
            )
        with open(config.AVERAGEWATCHTIMEPROPORTION, "a") as f:
            print(
                "writing average watch time proportion",
                str(self.compute_average_watch_time_proportion()),
            )
            f.write(
                str(timestamp)
                + " "
                + str(self.compute_average_watch_time_proportion())
                + "\n"
            )
        with open(config.AVERAGEWATCHMOVIERANK, "a") as f:
            print(
                "writing average rank of recommended movie watched",
                str(self.compute_movie_watched_rank()),
            )
            f.write(
                str(timestamp) + " " + str(self.compute_movie_watched_rank()) + "\n"
            )
        with open(config.RECOMMENDEDWATCHBYTOTALWATCH, "a") as f:
            print(
                "writing recommended watched by total watched",
                str(self.compute_recommended_watched_by_total_watched()),
            )
            f.write(
                str(timestamp)
                + " "
                + str(self.compute_recommended_watched_by_total_watched())
                + "\n"
            )
        with open(config.METRICFILE, "a") as f:
            f.write(
                str(timestamp)
                + "\n"
                + "Watch rate: "
                + str(self.compute_recommendation_watch_rate())
                + "\n"
                + "Good rating proportion: "
                + str(self.compute_recommendation_accuracy())
                + "\n"
                + "Average watch time proportion: "
                + str(self.compute_average_watch_time_proportion())
                + "\n"
                + "Avg watch rank: "
                + str(self.compute_movie_watched_rank())
                + "\n"
                + "recommended proportion in total watched: "
                + str(self.compute_recommended_watched_by_total_watched())
                + "\n"
                + " "
                + "\n"
            )

    def print_temp_metrics(self, timestamp):
        # Write the metrics to a file
        print("Watch rate: ", str(self.compute_recommendation_watch_rate()))

        print("Good rating percentage", str(self.compute_recommendation_accuracy()))

        print(
            "Average watch time proportion: ",
            str(self.compute_average_watch_time_proportion()),
        )

        print(
            "Average rank of recommended movie watched: ",
            str(self.compute_movie_watched_rank()),
        )

        print(
            "Recommended watched by total watched:",
            str(self.compute_recommended_watched_by_total_watched()),
        )

    def compute_recommendation_watch_rate(self):
        if self.num_of_recommendations == 0:
            return 0
        return self.recommended_watch_num / self.num_of_recommendations

    def compute_recommendation_accuracy(self):
        if self.total_recommendations_rated == 0:
            return 0
        return (
            self.recommended_movies_positive_rating / self.total_recommendations_rated
        )

    def compute_average_watch_time_proportion(self):
        if self.recommended_movie_length == 0:
            return 0
        return self.recommended_watch_time / self.recommended_movie_length

    def compute_movie_watched_rank(self):
        if self.recommended_watch_num == 0:
            return 0
        return self.recommended_rank_sum / self.recommended_watch_num

    def compute_recommended_watched_by_total_watched(self):
        if self.total_watch_num == 0:
            return 0
        return self.recommended_watch_num / self.total_watch_num

    def save_telemetry(self):
        data = {
            "recommendations": [],
            "recommended_watch_num": [],
            "num_of_recommendations": [],
            "recommended_movies_positive_rating": [],
            "total_recommendations_rated": [],
            "recommended_watch_time": [],
            "recommended_movie_length": [],
            "total_watch_num": [],
            "recommended_rank_sum": [],
        }
        data["recommendations"].append(self.recommendations)
        data["recommended_watch_num"].append(self.recommended_watch_num)
        data["num_of_recommendations"].append(self.num_of_recommendations)
        data["recommended_movies_positive_rating"].append(
            self.recommended_movies_positive_rating
        )
        data["total_recommendations_rated"].append(self.total_recommendations_rated)
        data["recommended_watch_time"].append(self.recommended_watch_time)
        data["recommended_movie_length"].append(self.recommended_movie_length)
        data["total_watch_num"].append(self.total_watch_num)
        data["recommended_rank_sum"].append(self.recommended_rank_sum)
        with open(config.TELEMETRYPATH, "w") as f:
            json.dump(data, f)

    def reset(self):
        self.recommendations = {}
        self.movie_watched_length = multi_dict(3, str)

        self.num_of_recommendations = 0
        self.recommended_watch_num = 0
        self.total_watch_num = 0

        self.recommended_watch_time = 0
        self.recommended_movie_length = 0

        self.recommended_movies_positive_rating = 0
        self.total_recommendations_rated = 0

        self.recommended_rank_sum = 0

    def setup_online_testing(self):
        server, topic = "fall2022-comp585.cs.mcgill.ca:9092", "movielog5"
        consumer = KafkaConsumer(
            topic, bootstrap_servers=[server], api_version=(0, 11, 5)
        )

        for message in consumer:
            self.parse_entry(message)
            # track 1000 recommendations for 12 hours
            if self.timestamp + self.timeinterval < int(time.time()):
                self.timestamp = int(time.time())
                if self.savedata:
                    self.write_metrics(self.timestamp)
                    self.save_telemetry()
                self.reset()


if __name__ == "__main__":
    OnlineEvaluation(3600, 1000)
