from flask import Flask

from src.model import Model

app = Flask(__name__)


@app.route("/recommend/<userid>")
def response(userid: str):
    r = Model.recommend(int(userid))
    result=""
    for i in range(20):
        result+=r[i]
        result+=","
    result=result[:-1]
    return result
