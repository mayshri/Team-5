import numpy as np
import pandas as pd
import torch
from spotlight.cross_validation import random_train_test_split
from spotlight.evaluation import sequence_mrr_score
from spotlight.interactions import Interactions
from spotlight.sequence.implicit import ImplicitSequenceModel

from . import config
from .utils import seed_everything


class Model:
    def __init__(self):

        seed_everything(config.SEED)
        self.model = ImplicitSequenceModel(
            n_iter=10,
            representation="cnn",
            loss="bpr",
        )

        self.interactions = pd.read_csv(config.INTERACTIONS)
        self.interactions["user_id"] = self.interactions["user_id"].astype("int32")

        try:
            self.movie_map = pd.read_csv(config.MOVIEMAP)
        except FileNotFoundError:
            print(
                "No movie map yet! The model must be trained first with model.train()"
            )
            self.movie_map = None

        self.top_20 = list(self.interactions["movie_id"].value_counts().head(20).index)
        self.users = set(self.interactions["user_id"].unique())

    def load_model(self):
        self.model = torch.load(config.MODEL)

    def train(self):
        movie_map_ids = pd.factorize(self.interactions["movie_id"])[0]
        movie_map_ids += 1
        self.interactions = self.interactions.assign(movie_map_id=movie_map_ids)

        dataset = Interactions(
            num_items=self.interactions["movie_map_id"].max() + 1,
            user_ids=self.interactions["user_id"].values,
            item_ids=self.interactions["movie_map_id"].values,
            timestamps=self.interactions["timestamp"].values,
        )

        train, test = random_train_test_split(dataset)

        train = train.to_sequence()
        test = test.to_sequence()

        self.model.fit(train, verbose=True)

        mrr_scores = sequence_mrr_score(self.model, test)
        print(mrr_scores)
        print(sum(mrr_scores) / len(mrr_scores))

        # Save model
        torch.save(self.model, config.MODEL)

        # Save movie map
        self.movie_map = pd.DataFrame(
            {
                "movie_id": self.interactions["movie_id"],
                "movie_map_id": self.interactions["movie_map_id"],
            }
        ).drop_duplicates()
        self.movie_map.to_csv(config.MOVIEMAP, index=False)

        return self.model

    def predict(self, movies, nbr_movies=10):
        movie_ids = [self.map_movie_id(movie) for movie in movies]
        pred = self.model.predict(sequences=np.array(movie_ids))
        indices = np.argpartition(pred, -nbr_movies)[-nbr_movies:]
        best_movie_id_indices = indices[np.argsort(pred[indices])]
        return [self.get_movie_id(movie) for movie in best_movie_id_indices]

    def recommend(self, user_id):
        if user_id not in self.users:
            return self.top_20
        else:
            movies = self.get_user_movies_watched(user_id)
            return self.predict(movies, 20)

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
