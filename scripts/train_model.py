import csv
import os

from kafka import KafkaConsumer

from src.utils.config import GIT_MODEL, KAFKA_DUMP, MOVIE_MAP
from src.inference.model import Model
from src.utils.process import ProcessDumps


def dump(amount: int):
    server = "fall2022-comp585.cs.mcgill.ca:9092"
    topic = "movielog5"

    consumer = KafkaConsumer(topic, bootstrap_servers=[server], api_version=(0, 11, 5))

    f = open(GIT_MODEL / KAFKA_DUMP, "w")
    writer = csv.writer(f)
    num = 0
    for message in consumer:
        if num >= amount:
            break
        num += 1
        writer.writerow(message)
    f.close()


def generate_interactions(amount: int):
    dump(amount)
    ProcessDumps.process_new_dump(GIT_MODEL / KAFKA_DUMP)


def train_model(amount: int):
    os.remove(GIT_MODEL / MOVIE_MAP)
    generate_interactions(amount)
    model = Model(GIT_MODEL, recompute_movie_map=True)
    train, test = model.load_interactions()
    model.fit(train)
    mrr_scores = model.eval(test)
    print(mrr_scores)


# specify the number of new entries you want to process
if __name__ == "__main__":
    n = 100000
    train_model(n)
