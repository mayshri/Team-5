from pathlib import Path
from typing import Optional, Set

import numpy as np
import pandas as pd
import torch
import torch.optim as optim
from spotlight.cross_validation import user_based_train_test_split
from spotlight.evaluation import sequence_mrr_score
from spotlight.interactions import Interactions
from spotlight.losses import adaptive_hinge_loss, bpr_loss, hinge_loss, pointwise_loss
from spotlight.sequence.implicit import ImplicitSequenceModel
from spotlight.sequence.representations import CNNNet, LSTMNet, MixtureLSTMNet, PoolNet
from spotlight.torch_utils import gpu

from src import config
from src.utils import seed


class ModelNotAvailable(Exception):
    pass


def our_initialization(self, interactions):

    sequences = interactions.sequences.astype(np.int64)
    # + 1 for 0, and +1 for the final index.
    self._num_items = sequences.max() + 2

    if self._representation == "pooling":
        self._net = PoolNet(self._num_items, self._embedding_dim, sparse=self._sparse)
    elif self._representation == "cnn":
        self._net = CNNNet(self._num_items, self._embedding_dim, sparse=self._sparse)
    elif self._representation == "lstm":
        self._net = LSTMNet(self._num_items, self._embedding_dim, sparse=self._sparse)
    elif self._representation == "mixture":
        self._net = MixtureLSTMNet(
            self._num_items, self._embedding_dim, sparse=self._sparse
        )
    else:
        self._net = self._representation

    self._net = gpu(self._net, self._use_cuda)

    if self._optimizer_func is None:
        self._optimizer = optim.Adam(
            self._net.parameters(), weight_decay=self._l2, lr=self._learning_rate
        )
    else:
        self._optimizer = self._optimizer_func(self._net.parameters())

    if self._loss == "pointwise":
        self._loss_func = pointwise_loss
    elif self._loss == "bpr":
        self._loss_func = bpr_loss
    elif self._loss == "hinge":
        self._loss_func = hinge_loss
    else:
        self._loss_func = adaptive_hinge_loss


ImplicitSequenceModel._check_input = lambda *args, **kwargs: None


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

    def __init__(self, model_folder: Path, recompute_movie_map: bool = False):

        seed.seed_everything(config.SEED)

        self.model_exists = False

        self.model_folder = model_folder

        self.model: ImplicitSequenceModel = None
        self.interactions: pd.DataFrame = None
        self.movie_map: pd.DataFrame = None
        self.top_20: Optional[str] = None
        self.users: Optional[Set] = None

        self.reload(recompute_movie_map)

    def reload(self, recompute_movie_map: bool = False):
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
            if recompute_movie_map:
                pd.DataFrame(
                    {
                        "movie_id": self.interactions["movie_id"],
                        "movie_map_id": self.interactions["movie_map_id"],
                    }
                ).drop_duplicates().to_csv(
                    self.model_folder / config.MOVIE_MAP, index=False
                )

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
        our_initialization(self.model, train)
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
        raise self.top_20

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
