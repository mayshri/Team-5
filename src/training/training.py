import os

from src.config import GIT_MODEL, MOVIE_MAP
from src.inference.model import Model


def online_model_training():
    os.remove(GIT_MODEL / MOVIE_MAP)
    model = Model(GIT_MODEL, recompute_movie_map=True)
    train, _ = model.load_interactions()
    model.fit(train)
