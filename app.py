import json

import requests
from flask import Flask

from src.model import Model

app = Flask(__name__)


@app.route("/recommend/<userid>")
def response(userid: str):
    r = Model.recommend(int(userid))
    result = {}
    for i in range(20):
        url = "http://fall2022-comp585.cs.mcgill.ca:8080/movie/" + r[i]
        result.update({i + 1: requests.get(url=url).json()})
    return json.dumps(result)
