import requests
from flask import Flask
from wrapt_timeout_decorator import timeout

app = Flask(__name__)


@app.route("/recommend/<userid>")
def response(userid: str):
    if not userid.isnumeric():
        return "invalid user", 404
    if int(userid) <= 0 or int(userid) > 1000000:
        return "invalid user", 404
    try:
        content, status_code = ask_inference(userid)
        if status_code == 200:
            return content
        else:
            # send_email(
            #     "[COMP585] Middleware ultimate backup plan triggered",
            #     "Middleware ultimate backup plan triggered",
            # )
            print("failed")
            return (
                "the+shawshank+redemption+1994,interstellar+2014,"
                "the+lord+of+the+rings+the+fellowship+of+the+ring+2001,inception+2010,"
                "the+lord+of+the+rings+the+two+towers+2002,"
                "the+lord+of+the+rings+the+return+of+the+king+2003,"
                "the+godfather+1972,star+wars+1977,pulp+fiction+1994,"
                "the+dark+knight+2008,the+green+mile+1999,"
                "spirited+away+2001,the+avengers+2012,seven+samurai+1954,the+matrix+1999,"
                "harry+potter+and+the+deathly+hallows+part+1+2010,"
                "the+dark+knight+rises+2012,fight+club+1999,"
                "howls+moving+castle+2004,whisper+of+the+heart+1995"
            )
    except Exception:
        # send email here
        # send_email(
        #     "[COMP585] Middleware ultimate backup plan triggered",
        #     "Middleware ultimate backup plan triggered!!! Time out!",
        # )
        print("too slow")
        return (
            "the+shawshank+redemption+1994,interstellar+2014,"
            "the+lord+of+the+rings+the+fellowship+of+the+ring+2001,inception+2010,"
            "the+lord+of+the+rings+the+two+towers+2002,"
            "the+lord+of+the+rings+the+return+of+the+king+2003,"
            "the+godfather+1972,star+wars+1977,pulp+fiction+1994,"
            "the+dark+knight+2008,the+green+mile+1999,"
            "spirited+away+2001,the+avengers+2012,seven+samurai+1954,the+matrix+1999,"
            "harry+potter+and+the+deathly+hallows+part+1+2010,"
            "the+dark+knight+rises+2012,fight+club+1999,"
            "howls+moving+castle+2004,whisper+of+the+heart+1995"
        )


@timeout(0.3)
def ask_inference(userid: str):
    reply = requests.get("http://inference:5001/recommend/" + userid)
    content, status_code = reply.content, reply.status_code
    return content, status_code
