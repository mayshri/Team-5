import shutil
import time

from flask import Flask, Response

from src import config
from src.inference.model import Model
from src.inference.recorder import Recorder
from src.utils.email_notification import send_email

app = Flask(__name__)

live_model = Model(config.LIVE_MODEL)
canary_model = Model(config.CANARY_MODEL)
g = Recorder()

# record the restart time stamp here.
MODEL_RELOADING = False


@app.route("/new_model_arrived/<commit_id>")
def reload(commit_id):
    global MODEL_RELOADING
    MODEL_RELOADING = True
    try:
        live_model.reload()
        canary_model.reload()
        # record reload here
        g.canary_time = int(time.time())
        g.canary_id = commit_id
        with open(config.DEPLOYED_MODELS / config.CANARY / config.CANARY_LOG, "a") as f:
            f.write(
                str(g.canary_time) + "," + str(commit_id) + ",new canary arrived" + "\n"
            )
        g.has_canary = True
        MODEL_RELOADING = False
        return "reload success"
    except Exception:
        return "reload failed"


@app.route("/online_evaluations")
def metric():
    try:
        with open(config.METRICFILE, "r") as f:
            text = f.read()
        return Response(text, mimetype="text/plain")
    except Exception:
        return "exception displaying online evaluation"


@app.route("/recommend/<userid>")
def response(userid: str):
    if not MODEL_RELOADING:
        if int(time.time()) - g.canary_time > 3600 and g.has_canary:
            with open(
                config.DEPLOYED_MODELS / config.CANARY / config.CANARY_LOG, "a"
            ) as f:
                f.write(
                    str(time.time())
                    + ","
                    + str(g.canary_id)
                    + ",new canary released"
                    + "\n"
                )
            with open(config.DEPLOYED_MODELS / config.LIVE / config.LIVE_LOG, "a") as f:
                f.write(
                    str(time.time())
                    + ","
                    + str(g.canary_id)
                    + ",new live deployed"
                    + "\n"
                )
            g.live_id = g.canary_id
            shutil.rmtree(config.LIVE_MODEL)
            # Copy the folder of current live model to canary model folder
            shutil.copytree(config.CANARY_MODEL, config.LIVE_MODEL)
            send_email(g.canary_id, "released")
            live_model.reload()
            g.has_canary = False

    if int(userid[-1]) <= 1:
        try:
            return canary_model.recommend(int(userid))
        except Exception:
            # abort canary here
            # send email
            if not MODEL_RELOADING:
                g.has_canary = False
                with open(
                    config.DEPLOYED_MODELS / config.CANARY / config.CANARY_LOG, "a"
                ) as f:
                    f.write(
                        str(time.time())
                        + ","
                        + str(g.canary_id)
                        + ",new canary abort"
                        + "\n"
                    )
                g.canary_id = g.live_id
                # Delete the folder of current canary model
                shutil.rmtree(config.CANARY_MODEL)
                # Copy the folder of current live model to canary model folder
                shutil.copytree(config.LIVE_MODEL, config.CANARY_MODEL)
                # Reload
                canary_model.reload()
                send_email(g.canary_id, "aborted")
                g.canary_id = g.live_id
            return live_model.recommend(int(userid))
    else:
        return live_model.recommend(int(userid))
