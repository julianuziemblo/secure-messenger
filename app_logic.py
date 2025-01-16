from typing import Any
import time


class AppLogic:
    def __init__(self, control: Any):
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            print('AppLogic thread running')
            time.sleep(1)

    def stop(self):
        self.running = False