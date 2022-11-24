from flask import Flask

from src import config
from src.inference.model import Model

app = Flask(__name__)

live_model = Model(config.LIVE_MODEL)
canary_model = Model(config.CANARY_MODEL)
# record the restart time stamp here.


@app.route("/new_model_arrived/<commit_id>")
def reload(commit_id):
    try:
        live_model.reload()
        canary_model.reload()
        # record reload here
        return "reload success"
    except Exception:
        return "reload failed"


@app.route("/recommend/<userid>")
def response(userid: str):
    if int(userid[-1]) <= 2:
        try:
            return canary_model.recommend(int(userid))
        except Exception:
            # abort canary here
            # send email
            return live_model.recommend(int(userid))
    else:
        return live_model.recommend(int(userid))
