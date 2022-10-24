import numpy as np
import pandas as pd
import torch
from spotlight.cross_validation import user_based_train_test_split
from spotlight.evaluation import sequence_mrr_score
from spotlight.interactions import Interactions
from spotlight.sequence.implicit import ImplicitSequenceModel
from kafka import KafkaConsumer

from . import config
from .utils import seed_everything


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

    def __init__(self):

        seed_everything(config.SEED)
        self.model = ImplicitSequenceModel(
            n_iter=10,
            representation="cnn",
            loss="bpr",
        )

        self.interactions = pd.read_csv(config.INTERACTIONS)
        self.interactions["user_id"] = self.interactions["user_id"].astype("int32")

        movie_map_ids = pd.factorize(self.interactions["movie_id"])[0]
        movie_map_ids += 1
        self.interactions = self.interactions.assign(movie_map_id=movie_map_ids)

        try:
            self.movie_map = pd.read_csv(config.MOVIEMAP)
        except FileNotFoundError:
            self.movie_map = pd.DataFrame(
                {
                    "movie_id": self.interactions["movie_id"],
                    "movie_map_id": self.interactions["movie_map_id"],
                }
            ).drop_duplicates()
            self.movie_map.to_csv(config.MOVIEMAP, index=False)

        self.top_20 = list(self.interactions["movie_id"].value_counts().head(20).index)
        self.users = set(self.interactions["user_id"].unique())

        self.setup_online_testing()

    def parse_entry(self, entry):
        print(entry)

    def setup_online_testing(self):
        server = "fall2022-comp585.cs.mcgill.ca:9092"
        topic = "movielog5"

        consumer = KafkaConsumer(topic, bootstrap_servers=[server], api_version=(0, 11, 5))

        for message in consumer:
            self.parse_entry(message)

    def load_model(self):
        self.model = torch.load(config.MODEL)

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
        train = train_interactions.to_sequence()
        self.model.fit(train, verbose=True)
        # Save model
        torch.save(self.model, config.MODEL)

    def eval(self, test_interactions: Interactions) -> np.ndarray:
        test = test_interactions.to_sequence()
        return sequence_mrr_score(self.model, test)

    def predict(self, movies, nbr_movies=10):
        movie_ids = [self.map_movie_id(movie) for movie in movies]
        pred = self.model.predict(sequences=np.array(movie_ids))
        indices = np.argpartition(pred, -nbr_movies)[-nbr_movies:]
        best_movie_id_indices = indices[np.argsort(pred[indices])]

        movies_recommended = [self.get_movie_id(movie) for movie in best_movie_id_indices]
        self.setup_online_testing(movies_recommended)
        return movies_recommended

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
