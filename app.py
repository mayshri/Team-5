from flask import Flask, Response

from src import config
from src.model import Model

app = Flask(__name__)

model = Model()
model.load_model()


@app.route("/recommend/online_evaluations")
def metric():
    with open(config.METRICFILE, "r") as f:
        text = f.read()
    return Response(text, mimetype="text/plain")


@app.route("/recommend/<userid>")
def response(userid: str):
    r = model.recommend(int(userid))
    result = ""
    for i in range(20):
        result += r[i]
        result += ","
    result = result[:-1]
    return result
