import time


class Recorder:
    def __init__(self):
        self.has_canary = False
        self.canary_time = int(time.time())
        self.canary_id = "default_canary"
        self.live_id = "default_live"
        self.release_canary = False
