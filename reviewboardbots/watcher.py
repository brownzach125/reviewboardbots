import time
from rbtools.api.client import RBClient
from datetime import datetime
from botmanager import BotManager

class Watcher:
    """The thing that watches review board for things"""
    def __init__(self,server):
        print("The watcher is born")
        self.client = RBClient(server)
        self.names_of_interest = self.getNamesOfInterest()
        self.bot_manager = BotManager("../bots", "../bot_scripts")

    def getNamesOfInterest(self):
        """who the watcher should watch for"""
        return [ 'zbrown', 'meangirl', 'nobody' ]

    def getNewReviews(self, timestamp):
        """get reviews after the timestamp"""
        print("Looking for reviews")
        root = self.client.get_root()
        requests = root.get_review_requests( time_added_from=timestamp)

        requests = Watcher.filterRequests(requests, self.names_of_interest)

        return requests

    @staticmethod
    def filterRequests(requests, watched_names):
        filtered_requests = {}
        for request in requests:
            for person in request.target_people:
                if person.title in watched_names:
                   if person.title not in filtered_requests:
                       filtered_requests[person.title] = []
                   filtered_requests[person.title].append(request)
        return filtered_requests

    def watch(self):
        """Periodically check for new reviews, spin off bots when needed"""

        "Until the end of time"
        print("I am watching")
        checked_last_at = datetime.utcnow().isoformat()
        while True:
            self.bot_manager.processNewReviews(self.getNewReviews(checked_last_at))

            "Update the last time we checked"
            checked_last_at = datetime.utcnow().isoformat()

            "TODO pick good wait time"
            time.sleep(10)


watcher = Watcher('http://pds-rbdev01')
watcher.watch()
