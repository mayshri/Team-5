import requests
from kafka import KafkaConsumer

from src import config


class online_evaluation:
    def __init__(self):

        self.recommendations = {}
        self.recommmended_movies_watched = 0
        self.total_recommendations = 0
        self.recommmended_movies_positive_rating = 0
        self.total_recommendations_rated = 0
        self.average_watch_time_proportion = 0
        self.num_movies_watched = 0
        self.total_rank_movie_watched = 0
        self.setup_online_testing()

    def parse_entry(self, entry):
        parsed = entry.value.decode().split(",")

        # timestamp = parsed[0]
        user_id = parsed[1]

        # If length is <= 3 then the request is either a /data/ or /rate/ request
        if len(parsed) <= 3:
            user_recommendations = self.recommendations.get(
                user_id
            )  # Get all recommendations for this user

            # If the user has no recommendations, then we return as we don't make use of this data
            if user_recommendations is None:
                return

            # We get the type of request
            # (is is_data_request = true then it is a /data/ request else it is a /rate/ request)
            is_data_request = parsed[2].find("/data/") != -1
            is_rating_request = parsed[2].find("/rate/") != -1
            # we get the movie id from the request

            # If it is a /data/ request, we want to compute the "Recommended Movie Watch" Rate
            # If it is a /data/ request, we want to compute the "Average watch time proportion"
            if is_data_request:
                movie_id = parsed[2].split("/")[3]
                if movie_id in user_recommendations:
                    self.recommmended_movies_watched += 1
                    self.total_rank_movie_watched += (
                        user_recommendations.index(movie_id) + 1
                    )

                self.recommendations.pop(user_id)
                watch_time = parsed[2].split("/")[4]
                watch_time = int(watch_time.split(".")[0])
                movie_info = requests.get(
                    "http://fall2022-comp585.cs.mcgill.ca:8080/movie/" + movie_id
                ).json()
                if "runtime" not in movie_info:
                    return
                total_run_time = int(movie_info["runtime"])
                if total_run_time == 0:
                    return
                self.average_watch_time_proportion += watch_time / total_run_time
                self.num_movies_watched += 1
                return
            # If it is a /rate/ request, we want to compute the "Recommendation Accuracy" Rate
            elif is_rating_request:
                print(parsed, parsed[2].split("/rate/"))
                movie_id = parsed[2].split("/rate/")[1]
                rating = movie_id.split("=")[1]
                movie_id = movie_id.split("=")[0]

                if movie_id in user_recommendations:
                    self.total_recommendations_rated += 1
                    if float(rating) >= 5:
                        self.recommmended_movies_positive_rating += 1
                self.recommendations.pop(user_id)
                return
            else:
                return

        # Parse the movies so we only get the movies id
        movies_recommended = parsed[4:24]
        movies_recommended[0] = movies_recommended[0].replace("result: ", "")
        movies_recommended = [s.strip() for s in movies_recommended]
        self.recommendations[user_id] = movies_recommended
        self.total_recommendations += 1
        return

    def write_metrics(self):
        # Write the metrics to a file
        with open(config.RECOMMENDEDMOVIEWATCHRATE, "w") as f:
            print("writing watch rate", str(self.compute_recommendation_watch_rate()))
            f.write(str(self.compute_recommendation_watch_rate()))

        with open(config.RECOMMENDEDMOVIEACCURACY, "w") as f:
            print("writing accuracy", str(self.compute_recommendation_accuracy()))
            f.write(str(self.compute_recommendation_accuracy()))

        with open(config.AVERAGEWATCHTIMEPROPORTION, "w") as f:
            print(
                "writing average watch time proportion",
                str(self.compute_average_watch_time_proportion()),
            )
            f.write(str(self.compute_average_watch_time_proportion()))
        with open(config.AVERAGEWATCHMOVIERANK, "w") as f:
            print(
                "writing average rank of recommended movie watched",
                str(self.compute_movie_watched_rank()),
            )
            f.write(str(self.compute_movie_watched_rank()))

    def compute_recommendation_watch_rate(self):
        print(self.recommmended_movies_watched, self.total_recommendations)
        if self.total_recommendations == 0:
            return 0
        return self.recommmended_movies_watched / self.total_recommendations

    def compute_recommendation_accuracy(self):
        print(
            self.recommmended_movies_positive_rating, self.total_recommendations_rated
        )
        if self.total_recommendations_rated == 0:
            return 0
        return (
            self.recommmended_movies_positive_rating / self.total_recommendations_rated
        )

    def compute_average_watch_time_proportion(self):
        if self.num_movies_watched == 0:
            return 0
        return round(self.average_watch_time_proportion / self.num_movies_watched, 4)

    def compute_movie_watched_rank(self):
        print(self.total_rank_movie_watched, self.recommmended_movies_watched)
        if self.recommmended_movies_watched == 0:
            return 0
        return self.total_rank_movie_watched / self.recommmended_movies_watched

    def setup_online_testing(self):
        server = "fall2022-comp585.cs.mcgill.ca:9092"
        topic = "movielog5"

        consumer = KafkaConsumer(
            topic, bootstrap_servers=[server], api_version=(0, 11, 5)
        )

        entries = 0
        for message in consumer:
            print(message)
            entries += 1
            self.parse_entry(message)
            if entries == 100000:
                entries = 0
                self.write_metrics()