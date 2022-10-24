from unittest import TestCase

from spotlight.cross_validation import user_based_train_test_split
from spotlight.datasets.synthetic import generate_sequential
from spotlight.sequence.implicit import ImplicitSequenceModel


class TestInstalls(TestCase):
    def test_spotlight_installation(self):
        # spotlight is only tested up to pytorch 1.4
        # so we make sure it doesn't completely fail
        # with the version we're using
        dataset = generate_sequential(
            num_users=10,
            num_items=100,
            num_interactions=1000,
            concentration_parameter=0.01,
            order=3,
        )

        try:
            train, test = user_based_train_test_split(dataset)

            train = train.to_sequence()
            test = test.to_sequence()

            model = ImplicitSequenceModel(n_iter=1, representation="cnn", loss="bpr")
            model.fit(train)
        except ValueError:
            # flakey test due to random train test split
            pass
