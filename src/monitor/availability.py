from kafka import KafkaConsumer

from src.utils.email_notification import send_email


class Availability:
    def __init__(self):
        self.monitor_availability()

    def check_statuscode(self, entry):
        parsed = entry.value.decode("utf-8").split(",")
        if (
            parsed[2].find(
                "recommendation request fall2022-comp585-5.cs.mcgill.ca:8082"
            )
            != -1
        ):
            if parsed[3].find("status 200") == -1:
                send_email(
                    "[COMP585] Recommendation failed status not 200",
                    entry.value.decode("utf-8"),
                )
                print(entry.value.decode("utf-8"))
        return

    def monitor_availability(self):
        server, topic = "fall2022-comp585.cs.mcgill.ca:9092", "movielog5"
        consumer = KafkaConsumer(
            topic, bootstrap_servers=[server], api_version=(0, 11, 5)
        )
        print("start monitoring availability")
        for message in consumer:
            self.check_statuscode(message)


if __name__ == "__main__":
    Availability()
