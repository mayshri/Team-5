import csv

from kafka import KafkaConsumer

from src.config import DUMP


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


# specify the number of entries you want to dump
amount = 100000
dump(amount)
