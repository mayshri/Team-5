import time

import pandas as pd
from kafka import KafkaConsumer

from src import config
from src.utils.process import (
    ProcessDumps,
    check_movie_id,
    check_timestamp,
    check_user_id,
)


class DataCollector:
    def __init__(self, save_period):
        self.save_period = save_period
        self.entries = []
        self.last_save_time = time.time()
        self.verified_movies = pd.read_csv(config.GIT_MODEL / config.VERIFIED_MOVIES)[
            "movie_id"
        ].tolist()
        self.start_data_collector()

    def save_entries(self):
        new_interactions_df = pd.DataFrame(
            self.entries, columns=["timestamp", "user_id", "movie_id"]
        )
        existing_interactions_df = pd.read_csv(
            config.GIT_MODEL / config.NEWINTERACTIONS
        )

        interactions_df = pd.concat(
            [existing_interactions_df, new_interactions_df], ignore_index=True
        )
        interactions_df.drop_duplicates(subset=["user_id", "movie_id"], inplace=True)
        interactions_df = interactions_df[
            pd.to_numeric(interactions_df["user_id"], errors="coerce").notnull()
        ]
        interactions_df.to_csv(config.GIT_MODEL / config.NEWINTERACTIONS, index=False)
        new_verify_movie = pd.DataFrame({"movie_id": self.verified_movies})
        new_verify_movie = new_verify_movie.drop_duplicates()
        new_verify_movie.to_csv(config.GIT_MODEL / config.VERIFIED_MOVIES, index=False)
        self.verified_movies = pd.read_csv(config.GIT_MODEL / config.VERIFIED_MOVIES)[
            "movie_id"
        ].tolist()
        self.entries = []
        self.last_save_time = time.time()

    def parse_entry(self, entry):
        df = entry.split(",")

        timestamp = df[0]
        user_id = df[1]
        movie_id = df[2].split("/")[3]

        if not check_timestamp(timestamp) or not check_user_id(user_id):
            return

        if movie_id not in self.verified_movies:
            if not check_movie_id(movie_id):
                return
            else:
                self.verified_movies.append(movie_id)

        timestamp = time.mktime(ProcessDumps.try_parsing_date(timestamp).timetuple())
        self.entries.append([timestamp, user_id, movie_id])

    def start_data_collector(self):
        server, topic = "fall2022-comp585.cs.mcgill.ca:9092", "movielog5"

        consumer = KafkaConsumer(
            topic, bootstrap_servers=[server], api_version=(0, 11, 5)
        )

        for message in consumer:
            msg = message.value.decode("utf-8")
            if self.last_save_time + self.save_period < time.time():
                self.save_entries()
            elif msg.find("/data/") != -1:
                self.parse_entry(msg)


if __name__ == "__main__":
    DataCollector(600)
