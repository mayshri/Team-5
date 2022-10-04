from pathlib import Path

import numpy as np
import pandas as pd
import torch
from spotlight.cross_validation import random_train_test_split
from spotlight.evaluation import sequence_mrr_score
from spotlight.interactions import Interactions
from spotlight.sequence.implicit import ImplicitSequenceModel

MODELSFOLDER = Path(__file__).parents[1] / "models"
MODEL = MODELSFOLDER / "model.pt"
MOVIEMAP = MODELSFOLDER / "movie_map.csv"

DATAFOLDER = Path(__file__).parents[1] / "data"
INTERACTIONS = DATAFOLDER / "interactions.csv"


class Model:
    @staticmethod
    def train(data_path: Path):
        data = pd.read_csv(data_path)

        data["user_id"] = data["user_id"].astype("int32")

        movie_map_ids = pd.factorize(data["movie_id"])[0]
        movie_map_ids += 1
        data = data.assign(movie_map_id=movie_map_ids)

        dataset = Interactions(
            num_items=data["movie_map_id"].max() + 1,
            user_ids=data["user_id"].values,
            item_ids=data["movie_map_id"].values,
            timestamps=data["timestamp"].values,
        )

        model = ImplicitSequenceModel(
            n_iter=10,
            representation="cnn",
            loss="bpr",
        )

        train, test = random_train_test_split(dataset)

        train = train.to_sequence()
        test = test.to_sequence()

        model.fit(train, verbose=True)

        mrr_scores = sequence_mrr_score(model, test)
        print(mrr_scores)
        print(sum(mrr_scores) / len(mrr_scores))

        # Save model
        torch.save(model, MODEL)

        # Save movie map
        pd.DataFrame(
            {"movie_id": data["movie_id"], "movie_map_id": data["movie_map_id"]}
        ).drop_duplicates().to_csv(MOVIEMAP, index=False)

        return model

    @staticmethod
    def map_movie_id(movie_id):
        movie_map = pd.read_csv(MOVIEMAP)
        return movie_map[movie_map["movie_id"] == movie_id]["movie_map_id"].values[0]

    @staticmethod
    def get_movie_id(mapped_movie_id):
        movie_map = pd.read_csv(MOVIEMAP)
        return movie_map[movie_map["movie_map_id"] == mapped_movie_id][
            "movie_id"
        ].values[0]

    @staticmethod
    def get_user_movies_watched(user_id):
        data = pd.read_csv(INTERACTIONS)

        return data[data["user_id"] == user_id]["movie_id"].values

    @staticmethod
    def predict(cls, movies, nbr_movies=10):

        if len(movies) == 0:
            data = pd.read_csv(INTERACTIONS)
            return list(data["movie_id"].value_counts().head(20).index)

        model = torch.load(MODEL)
        movie_ids = [cls.map_movie_id(movie) for movie in movies]

        pred = model.predict(sequences=np.array(movie_ids))
        indices = np.argpartition(pred, -nbr_movies)[-nbr_movies:]
        best_movie_id_indices = indices[np.argsort(pred[indices])]
        return [cls.get_movie_id(movie) for movie in best_movie_id_indices]

    @classmethod
    def recommend(cls, user_id):
        movies = cls.get_user_movies_watched(user_id)
        return cls.predict(cls, movies, 20)
