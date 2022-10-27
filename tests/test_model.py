from unittest import TestCase

import numpy as np

from src.model import Model


class TestModel(TestCase):
    def test_pretrained_model_evaluation(self):

        model = Model()
        model.load_model()

        _, test = model.load_interactions()

        mrr_scores = model.eval(test)

        print(f"\n Model Mean MRR score: {np.mean(mrr_scores)} \n")
        print(f"\n Model MRR score STD: {np.std(mrr_scores)} \n")
        print(f"\n Model best MRR score: {max(mrr_scores)} \n")
        print(f"\n Model worst MRR score: {min(mrr_scores)} \n")

    def test_model_training_and_evaluation(self):
        model = Model()

        train, test = model.load_interactions()
        model.fit(train)
        mrr_scores = model.eval(test)

        # let's make sure the watched movie is in the top
        # 100 movies on average (the top 0.7% of all movies)
        self.assertGreater(np.mean(mrr_scores), 0.001)
