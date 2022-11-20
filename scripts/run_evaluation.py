from src.monitor.monitor import OnlineEvaluation

if __name__ == "__main__":
    OnlineEvaluation(timeinterval=21600, online_evaluation_threshold=100)
