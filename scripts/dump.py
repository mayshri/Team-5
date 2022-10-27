import csv

from kafka import KafkaConsumer

server = "fall2022-comp585.cs.mcgill.ca:9092"
topic = "movielog5"

consumer = KafkaConsumer(topic, bootstrap_servers=[server], api_version=(0, 11, 5))

f = open("data/kafka-dump.csv", "w")
writer = csv.writer(f)

num = 0
for message in consumer:
    if num >= 900000:
        break

    num += 1
    writer.writerow(message)

f.close()
