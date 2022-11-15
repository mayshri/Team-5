from pathlib import Path

SEED = 42

# filenames
MODEL_NAME = "model.pt"
MOVIE_MAP = "movie_map.csv"
INTERACTIONS = "interactions.csv"
KAFKA_DUMP = "kafka-dump.csv"
VERIFIED_MOVIES = "verified_movie.csv"

GIT_MODEL = Path(__file__).parents[1] / "models"

METRICSFOLDER = Path(__file__).parents[1] / "metrics"
RECOMMENDEDMOVIEWATCHRATE = METRICSFOLDER / "recommended_movie_watch_rate.txt"
RECOMMENDEDMOVIEACCURACY = METRICSFOLDER / "recommended_movie_accuracy.txt"
AVERAGEWATCHTIMEPROPORTION = METRICSFOLDER / "average_watch_time_proportion.txt"
AVERAGEWATCHMOVIERANK = METRICSFOLDER / "average_watch_movie_rank.txt"
RECOMMENDEDWATCHBYTOTALWATCH = METRICSFOLDER / "recommended_by_total.txt"
METRICFILE = METRICSFOLDER / "metrics.txt"

TELEMETRYPATH = METRICSFOLDER / "telemetry.json"
