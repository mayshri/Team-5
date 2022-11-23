from datetime import datetime
from unittest import TestCase

import pandas as pd

from src.config import GIT_MODEL, INTERACTIONS


class TestInteractions(TestCase):
    def test_timestamp(self):

        interactions = pd.read_csv(GIT_MODEL / INTERACTIONS)

        self.assertEqual(
            set(interactions.columns), {"timestamp", "user_id", "movie_id"}
        )

        min_watch_time = interactions["timestamp"].min()
        max_watch_time = interactions["timestamp"].max()

        # all movies should be watched this year. This checks
        # that the timestamp column was correctly processed
        self.assertEqual(datetime.fromtimestamp(min_watch_time).year, 2022)
        self.assertEqual(datetime.fromtimestamp(max_watch_time).year, 2022)

    def test_user_id_is_numeric(self):

        interactions = pd.read_csv(GIT_MODEL / INTERACTIONS, dtype=str)
        self.assertEqual(
            set(interactions.columns), {"timestamp", "user_id", "movie_id"}
        )
        users = interactions.user_id.unique()
        for u in users:
            self.assertTrue(u.isnumeric())

    def test_user_id_is_valid(self):

        interactions = pd.read_csv(GIT_MODEL / INTERACTIONS)

        self.assertEqual(
            set(interactions.columns), {"timestamp", "user_id", "movie_id"}
        )

        users = interactions.user_id.unique()

        for u in users:
            self.assertGreaterEqual(u, 1)
            self.assertLessEqual(u, 1000000)
