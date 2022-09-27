from pathlib import Path
from tabnanny import verbose
from typing import Union

import torch
import pandas as pd

from spotlight.sequence.implicit import ImplicitSequenceModel
from spotlight.interactions import Interactions
from spotlight.cross_validation import random_train_test_split
from spotlight.evaluation import rmse_score

MODELSFOLDER = Path(__file__).parents[1] / "models"
MODEL = MODELSFOLDER / "model.pt"
MOVIEMAP = MODELSFOLDER / "movie_map.csv"

class Model:

    @staticmethod
    def train(data: Path):
        data = pd.read_csv(data)

        data['user_id'] = data['user_id'].astype('int32')

        movie_map_ids = pd.factorize(data['movie_id'])[0]
        movie_map_ids += 1
        data = data.assign(movie_map_id=movie_map_ids)

        dataset = Interactions(
            num_items=data['movie_map_id'].max()+1,
            user_ids=data['user_id'].values,
            item_ids=data['movie_map_id'].values,
            timestamps=data['timestamp'].values
        )

        model = ImplicitSequenceModel(
            n_iter=10,
            representation='cnn',
            loss='bpr',
        )

        train, test = random_train_test_split(dataset)

        train = train.to_sequence()
        test = test.to_sequence()

        model.fit(train, verbose=True)

        # Save model
        torch.save(model, MODEL)

        # Save movie map
        pd.DataFrame({'movie_id': data['movie_id'], 'movie_map_id': data['movie_map_id']}).to_csv(MOVIEMAP, index=False)
        
        return model