from pathlib import Path
from unittest import TestCase

from src.process import ProcessDumps


class TestProcess(TestCase):
    def test_process_raw_dump(self):

        interactions = ProcessDumps.raw_to_interactions(
            Path(__file__).parent / "test-kafka-dump.csv"
        )
        self.assertEqual(len(interactions), 7)
        self.assertEqual(
            set(interactions.columns), {"timestamp", "user_id", "movie_id"}
        )
