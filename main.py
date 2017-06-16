#import json
import yaml
import logging
import os
import threading
import config

from botmanager import BotManager
from watcher import Watcher

logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)


class Service:
    def __init__(self):
        self.bot_manager = BotManager()
        self.watcher = Watcher(self.bot_manager)
        self.watcher_thread = None

    def start(self):
        print "Service: Start"
        self.watcher_thread = threading.Thread(target=self.watcher.watch)
        self.watcher_thread.start()
        self.bot_manager.start()

    def stop(self):
        print "Service: Stop"
        self.watcher.stop()
        self.bot_manager.stop()
        self.watcher_thread = None


service = Service()
service.start()
