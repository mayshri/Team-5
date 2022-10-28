import csv
import os

from kafka import KafkaConsumer

from src.config import DUMP, MOVIEMAP
from src.model import Model
from src.process import ProcessDumps


def dump(amount: int):
    server = "fall2022-comp585.cs.mcgill.ca:9092"
    topic = "movielog5"

    consumer = KafkaConsumer(topic, bootstrap_servers=[server], api_version=(0, 11, 5))

    f = open(DUMP, "w")
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
    ProcessDumps.process_new_dump(DUMP)


def train_model(amount: int):
    os.remove(MOVIEMAP)
    generate_interactions(amount)
    model = Model()
    train, test = model.load_interactions()
    model.fit(train)
    mrr_scores = model.eval(test)
    print(mrr_scores)


# specify the number of new entries you want to process
n = 100000
train_model(n)
