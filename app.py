from apscheduler.scheduler import Scheduler
from flask import Flask, Response

from src import config
from src.model import Model

app = Flask(__name__)

# this backup model does not get updated during
# deployment, since we will not be updating git
# (`git pull`) on the server
backup_model = Model(config.GIT_MODEL)

live_model = Model(config.LIVE_MODEL)
canary_model = Model(config.CANARY_MODEL)


cron = Scheduler(daemon=True)
# Explicitly kick off the background thread
cron.start()


# every 15 minutes, the flask app will check for
# updates to the models, and will update the
# respective models as necessary
@cron.interval_schedule(minutes=15)
def reload_models():
    live_model.reload()
    canary_model.reload()


@app.route("/recommend/online_evaluations")
def metric():
    with open(config.METRICFILE, "r") as f:
        text = f.read()
    return Response(text, mimetype="text/plain")


@app.route("/recommend/<userid>")
def response(userid: str):
    try:
        if int(userid[-1]) <= 2:
            return canary_model.recommend(int(userid))
        else:
            return live_model.recommend(int(userid))
    except Exception:
        return backup_model.recommend(int(userid))
