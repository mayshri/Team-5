from unittest import TestCase

import numpy as np

from src.model import Model


class TestModel(TestCase):
    def test_model_evaluation(self):

        model = Model()
        model.load_model()

        _, test = model.load_interactions()

        mrr_scores = model.eval(test)

        print(f"\n Model Mean MRR score: {np.mean(mrr_scores)} \n")
        print(f"\n Model MRR score STD: {np.std(mrr_scores)} \n")
        print(f"\n Model best MRR score: {max(mrr_scores)} \n")
        print(f"\n Model worst MRR score: {min(mrr_scores)} \n")
