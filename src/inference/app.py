from apscheduler.scheduler import Scheduler
from flask import Flask, Response

from src import config
from src.inference.model import Model

app = Flask(__name__)

live_model = Model(config.LIVE_MODEL)
canary_model = Model(config.CANARY_MODEL)

# 20% users will be assigned for testing the new model
user_class_round = [[0, 5], [1, 6], [2, 7], [3, 8], [4, 9]]
canary_round = 0

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
    # this bring more fairness
    if int(userid[-1]) in user_class_round[canary_round % 5]:
        try:
            return canary_model.recommend(int(userid))
        except Exception:
            return live_model.recommend(int(userid))
    else:
        return live_model.recommend(int(userid))
