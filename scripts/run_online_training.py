import sys
sys.path.append(".")

from src.data_collector.data_collector import OnlineTraining

if __name__ == "__main__":
    OnlineTraining(10)