import time
from kafka import KafkaConsumer
from src.process import check_timestamp, ProcessDumps
import pandas as pd
from src.github import GithubClient
from src import config

class OnlineTraining:
    def __init__(self, timeinterval):
        self.timeinterval = timeinterval
        self.entries = []
        self.last_update = time.time()
        self.github = GithubClient()
        self.setup_online_training()

    def save_entries(self):
        new_interactions_df = pd.DataFrame(self.entries, columns =['timestamp', 'user_id', 'movie_id'])
        existing_interactions_df = pd.read_csv(config.INTERACTIONS_PATH)

        interactions_df = pd.concat([existing_interactions_df, new_interactions_df], ignore_index=True)
        interactions_df.drop_duplicates(subset=['user_id', 'movie_id'], inplace=True)
        interactions_df.to_csv(config.INTERACTIONS_PATH, index=False)

        self.github.update_file(config.INTERACTIONS_PATH, "[ONLINE TRAINING] Update interactions - " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        self.entries = []
        self.last_update = time.time()

    def parse_entry(self, entry):
        df = entry.split(",")
        
        user_id = df[1]
        movie_id  = df[2].split("/")[3]
        timestamp = df[0]
        
        if not check_timestamp(timestamp):
            return

        timestamp = time.mktime(ProcessDumps.try_parsing_date(timestamp).timetuple())
        self.entries.append([timestamp, user_id, movie_id])

    def setup_online_training(self):
        server, topic = "fall2022-comp585.cs.mcgill.ca:9092", "movielog5"
        
        consumer = KafkaConsumer(
            topic, bootstrap_servers=[server], api_version=(0, 11, 5)
        )

        for message in consumer:
            msg = message.value.decode("utf-8")
            if self.last_update + self.timeinterval < time.time():
                self.save_entries()
            elif msg.find("/data/") != -1:
                self.parse_entry(msg)