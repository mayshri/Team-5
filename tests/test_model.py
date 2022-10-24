from unittest import TestCase

from src.model import Model


class TestModel(TestCase):
    def test_model_evaluation(self):

        model = Model()
        model.load_model()

        _, test = model.load_interactions()

        mrr_scores = model.eval(test)

        print(f"\n Model Mean MRR score: {sum(mrr_scores) / len(mrr_scores)} \n")
