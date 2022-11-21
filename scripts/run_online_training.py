import sys

sys.path.append(".")

from src.data_collector.data_collector import DataCollector  # noqa: E402

if __name__ == "__main__":
    DataCollector(900)
