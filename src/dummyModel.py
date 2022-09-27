import json


def inference(user: int):
    return json.dumps(
        {
            "user": user,
            "1": "movie1",
            "2": "movie2",
            "3": "movie3",
            "4": "movie4",
            "5": "movie5",
        }
    )
