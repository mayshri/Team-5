import requests
from flask import Flask
from wrapt_timeout_decorator import timeout
import sendgrid
from sendgrid.helpers.mail import Mail

app = Flask(__name__)
with open("/middleware/SENDGRID_API_KEY.txt", "r") as f:
    key = f.readline()

@app.route("/recommend/<userid>")
def response(userid: str):
    try:
        content, status_code = ask_inference(userid)
        if status_code == 200:
            return content
        else:
            send_email(
                "[COMP585] Middleware ultimate backup plan triggered",
                "Middleware ultimate backup plan triggered",
            )
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
                "howls+moving+castle+2004,whisper+of+the+heart+1995 "
            )
    except Exception:
        # send email here
        send_email(
            "[COMP585] Middleware ultimate backup plan triggered",
            "Middleware ultimate backup plan triggered!!!",
        )
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
            "howls+moving+castle+2004,whisper+of+the+heart+1995 "
        )


@timeout(0.3)
def ask_inference(userid: str):
    reply = requests.get("http://inference:5001/" + userid)
    content, status_code = reply.content, reply.status_code
    return content, status_code

def send_email(subject: str, html_content: str):
    message = Mail(
        from_email="yuanye20001205@outlook.com",
        to_emails=[
            "qihan.wu@mail.mcgill.ca",
        ],
        subject=subject,
        html_content=html_content,
    )
    api_key = key
    sg = sendgrid.SendGridAPIClient(api_key=api_key)
    response = sg.send(message)
    print(response.status_code)
    print(response.body)
    print(response.headers)