import sendgrid
from sendgrid.helpers.mail import Mail

from src.config import API_KEY


def send_email(subject: str, html_content: str):
    message = Mail(
        from_email="yuanye20001205@outlook.com",
        to_emails=[
            "ye.yuan3@mail.mcgill.ca",
            "arthur.monnier@mail.mcgill.ca",
            "mayank.shrivastava@mail.mcgill.ca",
            "gabriel.tseng@mail.mcgill.ca",
            "qihan.wu@mail.mcgill.ca",
        ],
        subject=subject,
        html_content=html_content,
    )
    try:
        with open(API_KEY, "r") as f:
            key = f.readline()
        api_key = key
        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)
