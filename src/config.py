from pathlib import Path

SEED = 42

MODELSFOLDER = Path(__file__).parents[1] / "models"
MODEL = MODELSFOLDER / "model.pt"
MOVIEMAP = MODELSFOLDER / "movie_map.csv"

DATAFOLDER = Path(__file__).parents[1] / "data"
INTERACTIONS = DATAFOLDER / "interactions.csv"
