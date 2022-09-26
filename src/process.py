from pathlib import Path
from typing import Union

import pandas as pd

DATAFOLDER = Path(__file__).parents[1] / "data"
RATINGS = DATAFOLDER / "ratings.csv"


class ProcessDumps:

    """
    Usage:
    ```
    >>> from src.process import ProcessDumps, DATAFOLDER
    >>> ProcessDumps.process_new_dump("kafka-dump.csv")
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
    def raw_to_interactions(raw_dump: Path) -> pd.DataFrame:
        dump_df = pd.read_csv(raw_dump, header=None)

        data = dump_df[6]
        df = data.str.split(",", 2, expand=True)
        df.columns = ["timestamp", "user_id", "request"]

        # Filter by 'rating' requests
        df = df.loc[df["request"].str.find("/data/") != -1]

        # Clean data
        df[["request", "rating"]] = df["request"].str.split("=", expand=True)
        df["movie_id"] = df["request"].str.split("/", expand=True)[3]
        df = df.drop(labels=["request"], axis=1)
        return df

    @classmethod
    def process_new_dump(cls, raw_dump: Union[Path, str]) -> None:

        new_interactions = cls.raw_to_interactions(Path(raw_dump))
        new_ratings = cls.raw_to_ratings(Path(raw_dump))

        new_data = pd.concat([new_ratings, new_interactions])
        if not RATINGS.exists():
            new_data.to_csv(RATINGS, index=False)

        combined_ratings = pd.concat([new_data, pd.read_csv(RATINGS)]).drop_duplicates()
        combined_ratings.to_csv(RATINGS, index=False)
