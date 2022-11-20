import datetime
import time

import pandas as pd
from kafka import KafkaConsumer

from src import config
from src.training.training import online_model_training
from src.utils.github import GithubClient
from src.utils.process import ProcessDumps, check_timestamp


class OnlineTraining:
    def __init__(self, timeinterval):
        self.timeinterval = timeinterval
        self.max_interactions = 10000000

        self.entries = []
        self.last_update = time.time()
        self.github = GithubClient()
        self.setup_online_training()

    def save_entries(self):
        new_interactions_df = pd.DataFrame(
            self.entries, columns=["timestamp", "user_id", "movie_id"]
        )
        existing_interactions_df = pd.read_csv(config.GIT_MODEL / config.INTERACTIONS)

        interactions_df = pd.concat(
            [existing_interactions_df, new_interactions_df], ignore_index=True
        )
        interactions_df.drop_duplicates(subset=["user_id", "movie_id"], inplace=True)
        interactions_df = interactions_df[
            pd.to_numeric(interactions_df["user_id"], errors="coerce").notnull()
        ]

        # Handle the case where the number of interactions is too large
        # by keeping only the most recent interactions
        overflow = interactions_df.shape[0] - self.max_interactions
        if overflow > 0:
            interactions_df = interactions_df.iloc[overflow:]

        interactions_df.to_csv(config.GIT_MODEL / config.INTERACTIONS, index=False)

        # Train the model with the new interactions
        online_model_training()

        self.github.update_files(
            [
                (config.INTERACTIONS_PATH, "utf-8"),
                (config.MODEL_PATH, "base64"),
                (config.MOVIE_MAP_PATH, "utf-8"),
            ],
            "[ONLINE TRAINING] Update Interactions / Model / Movie Map - "
            + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        print("Online Training: Updated Interactions / Model / Movie Map")

        self.entries = []
        self.last_update = time.time()

    def parse_entry(self, entry):
        df = entry.split(",")

        user_id = df[1]
        movie_id = df[2].split("/")[3]
        timestamp = df[0]

        if not check_timestamp(timestamp):
            return

        timestamp = time.mktime(ProcessDumps.try_parsing_date(timestamp).timetuple())
        self.entries.append([timestamp, user_id, movie_id])

    def setup_online_training(self):
        server, topic = "fall2022-comp585.cs.mcgill.ca:9092", "movielog5"

        consumer = KafkaConsumer(
            topic, bootstrap_servers=[server], api_version=(0, 11, 5)
        )

        for message in consumer:
            msg = message.value.decode("utf-8")
            if self.last_update + self.timeinterval < time.time():
                self.save_entries()
            elif msg.find("/data/") != -1:
                self.parse_entry(msg)
