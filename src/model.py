import numpy as np
import pandas as pd
from pathlib import Path
import torch
from spotlight.cross_validation import user_based_train_test_split
from spotlight.evaluation import sequence_mrr_score
from spotlight.interactions import Interactions
from spotlight.sequence.implicit import ImplicitSequenceModel

from src import config, utils

from typing import Set


class ModelNotAvailable(Exception):
    pass


class Model:
    """
    Train the model using the following script:
    ```python
    model = Model()
    train, test = model.load_interactions()
    model.fit(train)
    mrr_scores = model.eval(test)
    ```

    And you can evaluate a trained model using the following script:
    ```python
    model = Model()
    model.load_model()
    train, test = model.load_interactions()
    model.eval(test)
    ```
    """

    def __init__(self, model_folder: Path):

        utils.seed_everything(config.SEED)

        self.model_exists = False

        self.model_folder = model_folder

        self.model: ImplicitSequenceModel = None
        self.interactions: pd.DataFrame = None
        self.movie_map: pd.DataFrame = None
        self.top_20: str = None
        self.users: Set = None

        self.reload()

    def reload(self):
        if self.model_folder.exists():
            self.model_exists = True
            self.model = ImplicitSequenceModel(
                n_iter=10,
                representation="cnn",
                loss="bpr",
            )

            self.interactions = pd.read_csv(self.model_folder / config.INTERACTIONS)
            self.interactions["user_id"] = self.interactions["user_id"].astype("int32")

            movie_map_ids = pd.factorize(self.interactions["movie_id"])[0]
            movie_map_ids += 1
            self.interactions = self.interactions.assign(movie_map_id=movie_map_ids)
            self.movie_map = pd.read_csv(self.model_folder / config.MOVIE_MAP)

            self.top_20 = self._process_predictions(
                list(self.interactions["movie_id"].value_counts().head(20).index)
            )
            self.users = set(self.interactions["user_id"].unique())

            self.model = torch.load(self.model_folder / config.MODEL_NAME)
        else:
            self.model_exists = False

    def load_interactions(self):
        dataset = Interactions(
            num_items=self.interactions["movie_map_id"].max() + 1,
            user_ids=self.interactions["user_id"].values,
            item_ids=self.interactions["movie_map_id"].values,
            timestamps=self.interactions["timestamp"].values,
        )
        train, test = user_based_train_test_split(
            dataset, random_state=np.random.RandomState(seed=config.SEED)
        )
        return train, test

    def fit(self, train_interactions: Interactions) -> None:
        # fit should always be saved in the git folder
        train = train_interactions.to_sequence()
        self.model.fit(train, verbose=True)
        # Save model
        torch.save(self.model, config.GIT_MODEL / config.MODEL_NAME)

    def eval(self, test_interactions: Interactions) -> np.ndarray:
        test = test_interactions.to_sequence()
        return sequence_mrr_score(self.model, test)

    def predict(self, movies, nbr_movies=10):
        movie_ids = [self.map_movie_id(movie) for movie in movies]
        pred = self.model.predict(sequences=np.array(movie_ids))
        indices = np.argpartition(pred, -nbr_movies)[-nbr_movies:]
        best_movie_id_indices = indices[np.argsort(pred[indices])]
        return [self.get_movie_id(movie) for movie in best_movie_id_indices]

    @staticmethod
    def _process_predictions(predictions):
        result = ""
        for i in range(20):
            result += predictions[i]
            result += ","
        result = result[:-1]
        return result

    def recommend(self, user_id):
        if self.model_exists:
            if user_id not in self.users:
                return self.top_20
            else:
                movies = self.get_user_movies_watched(user_id)
                return self._process_predictions(self.predict(movies, 20))
        raise ModelNotAvailable

    def map_movie_id(self, movie_id):
        return self.movie_map[self.movie_map["movie_id"] == movie_id][
            "movie_map_id"
        ].values[0]

    def get_movie_id(self, mapped_movie_id):
        return self.movie_map[self.movie_map["movie_map_id"] == mapped_movie_id][
            "movie_id"
        ].values[0]

    def get_user_movies_watched(self, user_id):
        return self.interactions[self.interactions["user_id"] == user_id][
            "movie_id"
        ].values
