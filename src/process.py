import csv
import datetime
import time
from pathlib import Path
from typing import Union

import pandas as pd
import requests

from src.config import VERIFY

DATAFOLDER = Path(__file__).parents[1] / "data"
INTERACTIONS = DATAFOLDER / "interactions.csv"


class ProcessDumps:
    """
    Usage:
    ```
    >>> from src.process import ProcessDumps
    >>> ProcessDumps.process_new_dump("data/kafka-dump.csv")
    ```
    """

    @staticmethod
    def raw_to_ratings(raw_dump: Path) -> pd.DataFrame:
        dump_df = pd.read_csv(raw_dump, header=None)

        data = dump_df[6]
        df = data.str.split(",", 2, expand=True)
        df.columns = ["timestamp", "user_id", "request"]

        # Filter by 'rating' requests
        df = df.loc[df["request"].str.find("/rate/") != -1]

        # Clean data
        df[["request", "rating"]] = df["request"].str.split("=", expand=True)
        df["movie_id"] = df["request"].str.split("/", expand=True)[2]
        df["rating"] = df["rating"].map(lambda x: x.rstrip("'"))
        df = df.drop(labels=["request"], axis=1)

        return df

    @staticmethod
    def check_timestamp(text):
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S.%3fZ"):
            try:
                datetime.datetime.strptime(text, fmt)
                return True
            except ValueError:
                pass
        return False

    @staticmethod
    def try_parsing_date(text):
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S.%3fZ"):
            try:
                return datetime.datetime.strptime(text, fmt)
            except ValueError:
                pass
        raise ValueError("no valid date format found")

    @classmethod
    def raw_to_interactions(cls, raw_dump: Path) -> pd.DataFrame:
        dump_df = pd.read_csv(raw_dump, header=None)
        data = dump_df[6]
        df = data.str.split(",", 2, expand=True)
        df.columns = ["timestamp", "user_id", "request"]

        # Filter by 'rating' requests
        df = df.loc[df["request"].str.find("/data/") != -1]

        # Clean data
        df["movie_id"] = df["request"].str.split("/", expand=True)[3]
        df["timestamp"] = df["timestamp"].map(
            lambda x: time.mktime(cls.try_parsing_date(x.replace("b'", "")).timetuple())
        )
        df = df.drop(labels=["request"], axis=1).drop_duplicates(
            subset=["user_id", "movie_id"]
        )

        verify_data = pd.read_csv(VERIFY)
        verified_movies = verify_data["movie_id"].tolist()

        with open(VERIFY, "a") as f:
            writer = csv.writer(f, delimiter=",")
            movielist = list(dict.fromkeys(df["movie_id"].tolist()))
            for movie_id in movielist:
                if movie_id in verified_movies:
                    pass
                else:
                    code = requests.get(
                        "http://fall2022-comp585.cs.mcgill.ca:8080/movie/" + movie_id
                    ).status_code
                    if code == 200:
                        verified_movies.append(movie_id)
                        writer.writerow([movie_id])
                    else:
                        df = df.drop(df.loc[df["movie_id"] == movie_id].index)
        return df

    @classmethod
    def process_new_dump(cls, raw_dump: Union[Path, str]) -> None:

        new_interactions = cls.raw_to_interactions(Path(raw_dump))

        if not INTERACTIONS.exists():
            new_interactions.to_csv(INTERACTIONS, index=False)
        else:
            combined_ratings = pd.concat(
                [new_interactions, pd.read_csv(INTERACTIONS)]
            ).drop_duplicates()
            combined_ratings.to_csv(INTERACTIONS, index=False)
