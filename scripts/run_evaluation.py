import sys

sys.path.append(".")

from src.monitor.monitor import OnlineEvaluation  # noqa: E402

if __name__ == "__main__":
    OnlineEvaluation(43200, 1000)
