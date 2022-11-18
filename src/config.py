from pathlib import Path

SEED = 42

MODELSFOLDER = Path(__file__).parents[1] / "models"
MODEL = MODELSFOLDER / "model.pt"
MOVIEMAP = MODELSFOLDER / "movie_map.csv"

DATAFOLDER = Path(__file__).parents[1] / "data"
INTERACTIONS = DATAFOLDER / "interactions.csv"
DUMP = DATAFOLDER / "kafka-dump.csv"
VERIFY = DATAFOLDER / "verified_movie.csv"

METRICSFOLDER = Path(__file__).parents[1] / "metrics"
RECOMMENDEDMOVIEWATCHRATE = METRICSFOLDER / "recommended_movie_watch_rate.txt"
RECOMMENDEDMOVIEACCURACY = METRICSFOLDER / "recommended_movie_accuracy.txt"
AVERAGEWATCHTIMEPROPORTION = METRICSFOLDER / "average_watch_time_proportion.txt"
AVERAGEWATCHMOVIERANK = METRICSFOLDER / "average_watch_movie_rank.txt"
RECOMMENDEDWATCHBYTOTALWATCH = METRICSFOLDER / "recommended_by_total.txt"
METRICFILE = METRICSFOLDER / "metrics.txt"

TELEMETRYPATH = METRICSFOLDER / "telemetry.json"

INTERACTIONS_PATH = "data/interactions.csv"
