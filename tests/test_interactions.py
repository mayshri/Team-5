from unittest import TestCase

import pandas as pd

from src.config import INTERACTIONS


class TestInteractions(TestCase):
    def test_interactions_data_quality(self):

        interactions = pd.read_csv(INTERACTIONS)

        self.assertEqual(
            set(interactions.columns), {"timestamp", "user_id", "movie_id"}
        )
