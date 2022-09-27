import requests
from flask import Flask

from src.dummyModel import inference

app = Flask(__name__)


@app.route("/recommend/<userid>")
def recommand(userid: str):
    url = "http://fall2022-comp585.cs.mcgill.ca:8080/user/" + userid
    respond = requests.get(url=url)
    r = inference(respond.json())
    return r
