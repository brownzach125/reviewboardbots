import time
import logging
import traceback
from rbtools.api.client import RBClient
import rbtools
import datetime
import config
from WatcherMemory import WatcherMemory


def parse_server_time_stamp(timestamp):
    return datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")


class Watcher:
    """The thing that watches review board for things"""
    def __init__(self, bot_manager):
        print("The watcher is born")
        self.creds = config.config['creds']
        self.server = config.config['review_board_server']
        self.client = RBClient(self.server, username=self.creds['username'], password=self.creds['password'])

        self.bot_name_list = config.config['bots'].keys()

        self.bot_manager = bot_manager
        self.requests_seen = {}
        self.keep_watching = False
        # TODO make a configuration
        # Protect against non existance
        self.bot_food_path = "./botfood_folder"
        self.memory = WatcherMemory(self.client, self.bot_food_path, self.bot_name_list)

    # Get new requests from the reviewboard server
    # Same as old function, but with smarter approach
    def get_new_requests(self):
        root = self.client.get_root()

        # TODO do I need to remove duplicates???
        requests = []
        for bot_name in self.bot_name_list:
            try:
                requests += root.get_review_requests(to_users=bot_name)
            except rbtools.api.errors.APIError as error:
                if error.message != "Object does not exist":
                    raise error

        logging.info("list of requests after filtering by bot names " + str([request["id"] for request in requests]))
        return requests

    def watch(self):
        """Periodically check for new reviews, spin off bots when needed"""
        self.keep_watching = True

        "Until my watch is ended"
        print("Watcher: I am watching")
        while self.keep_watching:
            try:
                # Get new requests from reviewboard server
                new_requests = self.get_new_requests()
                # Add those requets to the database
                self.memory.add_requests(new_requests, self.client)
                # Ask the database for requests that need "attention"
                requests_in_need_of_attention = self.memory.fresh_requests()

                # Handle those requests
                if requests_in_need_of_attention:
                    self.bot_manager.process_new_requests(requests_in_need_of_attention)
                    self.memory.mark_attended(requests_in_need_of_attention)
            except Exception as err:
                # If something goes wrong, create a new client and move on.
                # It's a little too broad, but it should keep the lights on.
                self.client = RBClient(self.server, username=self.creds['username'], password=self.creds['password'])
                traceback.print_exc()

                logging.error("The watcher encountered an error while polling")
            time.sleep(config.config['polling_wait_time'])

        print("Watcher: My watch has ended")

    def stop(self):
        self.keep_watching = False
        # TODO need to join
