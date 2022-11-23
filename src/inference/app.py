from flask import Flask, Response

from src import config
from src.inference.model import Model

app = Flask(__name__)

live_model = Model(config.LIVE_MODEL)
canary_model = Model(config.CANARY_MODEL)
# record the restart time stamp here.


@app.route("/recommend/online_evaluations")
def metric():
    with open(config.METRICFILE, "r") as f:
        text = f.read()
    return Response(text, mimetype="text/plain")


@app.route("/recommend/<userid>")
def response(userid: str):
    if int(userid[-1]) <= 2:
        try:
            return canary_model.recommend(int(userid))
        except Exception:
            return live_model.recommend(int(userid))
    else:
        return live_model.recommend(int(userid))
