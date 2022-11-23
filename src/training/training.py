import datetime
import os
import time
from threading import Timer

from src import config
from src.inference.model import Model
from src.utils.github import GithubClient


class AutoTraining:
    def __init__(self, train_period: int, instant_update=False):
        self.train_period = train_period
        self.github = GithubClient()
        self.last_train_time = time.time()

        if instant_update:
            self.model_training()
            self.push_new_model()

        self.set_up_autotraining()

    @staticmethod
    def model_training():
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
    AutoTraining(259020, False)
