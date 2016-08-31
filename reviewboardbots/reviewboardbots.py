from watcher import Watcher
from botmanager import BotManager
import threading
import json
import time
import os


class Service:
    def __init__(self, config_file_path):
        with open(config_file_path, 'r') as data_file:
            self.config= json.load(data_file)

        if 'review_board_server' not in self.config:
            raise ValueError('Must set review_board_server')

        if 'bots' not in self.config:
            raise ValueError('bots object must at least exist')

        bot_name_list = []
        bot_dict = {}
        for bot in self.config['bots']:
            bot_name_list.append(bot['name'])
            bot_dict[bot['name']] = bot

        self.bot_manager = BotManager(bot_dict)
        self.watcher = Watcher(self.config['review_board_server'], self.bot_manager, bot_name_list)
        self.watcher_thread = None

    def start(self):
        print "Service: Start"
        self.watcher_thread = threading.Thread(target=self.watcher.watch)
        self.watcher_thread.start()

    def stop(self):
        print "Service: Stop"
        self.watcher.stop()
        self.watcher_thread = None


service = Service(os.path.join("..","config.json"))
service.start()
