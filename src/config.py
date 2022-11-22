from pathlib import Path

SEED = 42

# folder names
MODELS_FOLDER = "models"

# filenames
MODEL_NAME = "model.pt"
MOVIE_MAP = "movie_map.csv"
INTERACTIONS = "interactions.csv"
KAFKA_DUMP = "kafka-dump.csv"
VERIFIED_MOVIES = "verified_movie.csv"

GIT_MODEL = Path(__file__).parents[1] / MODELS_FOLDER

# !! if this changes, it needs to change in the deployment.yml as well
DEPLOYED_MODELS = Path(__file__).parents[1] / "deployed_models"
LIVE_MODEL = DEPLOYED_MODELS / MODELS_FOLDER / "live"
CANARY_MODEL = DEPLOYED_MODELS / MODELS_FOLDER / "canary"
# !!

METRICSFOLDER = Path(__file__).parents[1] / "metrics"
RECOMMENDEDMOVIEWATCHRATE = METRICSFOLDER / "recommended_movie_watch_rate.txt"
RECOMMENDEDMOVIEACCURACY = METRICSFOLDER / "recommended_movie_accuracy.txt"
AVERAGEWATCHTIMEPROPORTION = METRICSFOLDER / "average_watch_time_proportion.txt"
AVERAGEWATCHMOVIERANK = METRICSFOLDER / "average_watch_movie_rank.txt"
RECOMMENDEDWATCHBYTOTALWATCH = METRICSFOLDER / "recommended_by_total.txt"
METRICFILE = METRICSFOLDER / "metrics.txt"

TELEMETRYPATH = METRICSFOLDER / "telemetry.json"

API_KEY = Path(__file__).parents[1] / "src" / "utils" / "SENDGRID_API_KEY.txt"
GITHUB_TOKEN = Path(__file__).parents[1] / "src" / "utils" / "GITHUB_TOKEN.txt"

INTERACTIONS_PATH = MODELS_FOLDER + "/" + INTERACTIONS
MODEL_PATH = MODELS_FOLDER + "/" + MODEL_NAME
MOVIE_MAP_PATH = MODELS_FOLDER + "/" + MOVIE_MAP
VERIFIED_MOVIES_PATH = MODELS_FOLDER + "/" + VERIFIED_MOVIES
