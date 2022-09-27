from pathlib import Path
from typing import Union

import pandas as pd

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
    def raw_to_interactions(raw_dump: Path) -> pd.DataFrame:
        dump_df = pd.read_csv(raw_dump, header=None)
        data = dump_df[6]
        df = data.str.split(",", 2, expand=True)
        df.columns = ["timestamp", "user_id", "request"]

        # Filter by 'rating' requests
        df = df.loc[df["request"].str.find("/data/") != -1]

        # Clean data
        df["movie_id"] = df["request"].str.split("/", expand=True)[3]
        df = df.drop(labels=["request"], axis=1).drop_duplicates(
            subset=["user_id", "movie_id"]
        )

        return df

    @classmethod
    def process_new_dump(cls, raw_dump: Union[Path, str]) -> None:

        new_interactions = cls.raw_to_interactions(Path(raw_dump))

        if not INTERACTIONS.exists():
            new_interactions.to_csv(INTERACTIONS, index=False)

        combined_ratings = pd.concat(
            [new_interactions, pd.read_csv(INTERACTIONS)]
        ).drop_duplicates()
        combined_ratings.to_csv(INTERACTIONS, index=False)
