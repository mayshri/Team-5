from flask import Flask

from src.model import Model
from src.online_evaluation import OnlineEvaluation

app = Flask(__name__)

model = Model()
model.load_model()


@app.route("/recommend/<userid>")
def response(userid: str):
    r = model.recommend(int(userid))
    result = ""
    for i in range(20):
        result += r[i]
        result += ","
    result = result[:-1]
    return result


OnlineEvaluation(43200, 1000)
