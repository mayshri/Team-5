import csv
import datetime
import time
from pathlib import Path
from typing import Union

import pandas as pd
import requests

from src.utils.config import GIT_MODEL, INTERACTIONS, VERIFIED_MOVIES

INTERACTIONS_PATH = GIT_MODEL / INTERACTIONS


def check_timestamp(text):
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
        try:
            datetime.datetime.strptime(text, fmt)
            return True
        except ValueError:
            pass
    return False


def check_user_id(user_id):
    if user_id.isnumeric():
        if 1 <= int(user_id) <= 1000000:
            return True
    return False


def check_movie_id(movie_id):
    code = requests.get(
        "http://fall2022-comp585.cs.mcgill.ca:8080/movie/" + movie_id
    ).status_code
    return code == 200


class ProcessDumps:
    """
    Usage:
    ```
    >>> from src.process import ProcessDumps
    >>> ProcessDumps.process_new_dump("data_collector/kafka-dump.csv")
    ```
    """

    """
    @staticmethod
    def raw_to_ratings(raw_dump: Path) -> pd.DataFrame:
        dump_df = pd.read_csv(raw_dump, header=None)

        data_collector = dump_df[6]
        df = data_collector.str.split(",", 2, expand=True)
        df.columns = ["timestamp", "user_id", "request"]

        # Filter by 'rating' requests
        df = df.loc[df["request"].str.find("/rate/") != -1]

        # Clean data_collector
        df[["request", "rating"]] = df["request"].str.split("=", expand=True)
        df["movie_id"] = df["request"].str.split("/", expand=True)[2]
        df["rating"] = df["rating"].map(lambda x: x.rstrip("'"))
        df = df.drop(labels=["request"], axis=1)

        return df
    """

    @staticmethod
    def try_parsing_date(text):
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M"):
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
        df = df.loc[df["request"].str.find("/data_collector/") != -1]

        # Clean data_collector
        df["movie_id"] = df["request"].str.split("/", expand=True)[3]
        df["timestamp"] = df["timestamp"].map(lambda x: x.replace("b'", ""))
        df = df[df.timestamp.apply(lambda x: check_timestamp(x))]
        df["timestamp"] = df["timestamp"].map(
            lambda x: time.mktime(cls.try_parsing_date(x).timetuple())
        )
        df = df.drop(labels=["request"], axis=1).drop_duplicates(
            subset=["user_id", "movie_id"]
        )
        df = df[df.user_id.apply(lambda x: check_user_id(x))]

        verify_data = pd.read_csv(GIT_MODEL / VERIFIED_MOVIES)
        verified_movies = verify_data["movie_id"].tolist()

        with open(GIT_MODEL / VERIFIED_MOVIES, "a") as f:
            writer = csv.writer(f, delimiter=",")
            movielist = list(dict.fromkeys(df["movie_id"].tolist()))
            for movie_id in movielist:
                if movie_id in verified_movies:
                    pass
                else:
                    if check_movie_id(movie_id):
                        verified_movies.append(movie_id)
                        writer.writerow([movie_id])
                    else:
                        df = df.drop(df.loc[df["movie_id"] == movie_id].index)
        return df

    @classmethod
    def process_new_dump(cls, raw_dump: Union[Path, str]) -> None:

        new_interactions = cls.raw_to_interactions(Path(raw_dump))

        if not INTERACTIONS_PATH.exists():
            new_interactions.to_csv(INTERACTIONS_PATH, index=False)
        else:
            combined_ratings = pd.concat(
                [new_interactions, pd.read_csv(INTERACTIONS_PATH)]
            ).drop_duplicates()
            combined_ratings.to_csv(INTERACTIONS_PATH, index=False)
