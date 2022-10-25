from datetime import datetime
from unittest import TestCase

import pandas as pd

from src.config import INTERACTIONS


class TestInteractions(TestCase):
    def test_interactions_data_quality(self):

        interactions = pd.read_csv(INTERACTIONS)

        self.assertEqual(
            set(interactions.columns), {"timestamp", "user_id", "movie_id"}
        )

        # we will subsample a number of rows and sanity check the movie
        # ids are in a format we expect
        movie_ids = interactions.sample(n=100).movie_id

        for movie in movie_ids:
            # all movie ids should end with the year.
            # this checks that the movies column was
            # correctly processed
            year = int(movie[-4:])
            # according to Wikipedia, the first movie to
            # reach "worldwide success" was in 1895
            self.assertGreater(year, 1894)
            # no movies can come from the future
            self.assertGreater(2023, year)

        min_watch_time = interactions["timestamp"].min()
        max_watch_time = interactions["timestamp"].max()

        # all movies should be watched this year. This checks
        # that the timestamp column was correctly processed
        self.assertEqual(datetime.fromtimestamp(min_watch_time).year, 2022)
        self.assertEqual(datetime.fromtimestamp(max_watch_time).year, 2022)
