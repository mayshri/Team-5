import datetime
import os
import time
from threading import Timer

import pandas as pd

from src import config
from src.inference.model import Model
from src.utils.github import GithubClient


class AutoTraining:
    def __init__(self, train_period: int, max_interactions: int, instant_update=False):
        self.train_period = train_period
        self.github = GithubClient()
        self.last_train_time = time.time()
        self.max_interactions = max_interactions

        if instant_update:
            self.model_training()
            self.push_new_model()

        self.set_up_autotraining()

    def model_training(self):
        new_interactions_df = pd.read_csv(config.GIT_MODEL / config.NEWINTERACTIONS)
        data = {"timestamp": [], "user_id": [], "movie_id": []}
        refresh_new_interactions_df = pd.DataFrame(data)
        refresh_new_interactions_df.to_csv(
            config.GIT_MODEL / config.NEWINTERACTIONS, index=False
        )
        existing_interactions_df = pd.read_csv(config.GIT_MODEL / config.INTERACTIONS)
        interactions_df = pd.concat(
            [existing_interactions_df, new_interactions_df], ignore_index=True
        )
        interactions_df.drop_duplicates(
            subset=["user_id", "movie_id"], keep="last", inplace=True
        )
        interactions_df = interactions_df[
            pd.to_numeric(interactions_df["user_id"], errors="coerce").notnull()
        ]
        overflow = interactions_df.shape[0] - self.max_interactions
        if overflow > 0:
            interactions_df = interactions_df.iloc[overflow:]
        interactions_df.to_csv(config.GIT_MODEL / config.INTERACTIONS, index=False)
        os.remove(config.GIT_MODEL / config.MOVIE_MAP)
        model = Model(config.GIT_MODEL, recompute_movie_map=True)
        train, _ = model.load_interactions()
        model.fit(train)

    def push_new_model(self):
        self.github.update_files(
            [
                (
                    config.GIT_MODEL / config.INTERACTIONS,
                    config.INTERACTIONS_PATH,
                    "utf-8",
                ),
                (config.GIT_MODEL / config.MODEL_NAME, config.MODEL_PATH, "base64"),
                (config.GIT_MODEL / config.MOVIE_MAP, config.MOVIE_MAP_PATH, "utf-8"),
                (
                    config.GIT_MODEL / config.VERIFIED_MOVIES,
                    config.VERIFIED_MOVIES_PATH,
                    "utf-8",
                ),
            ],
            "[ONLINE TRAINING] Update Interactions / Model / Movie Map / Verified Movie - "
            + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        print(
            "Online Training: Updated Interactions / Model / Movie Map / Verified Movie"
        )

    def auto_retrain(self):
        self.model_training()
        self.push_new_model()
        Timer(self.train_period, self.auto_retrain).start()

    def set_up_autotraining(self):
        time.sleep(self.train_period)
        self.auto_retrain()


if __name__ == "__main__":
    AutoTraining(86400, 10000000, False)
