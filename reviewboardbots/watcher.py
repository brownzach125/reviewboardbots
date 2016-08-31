import time
from rbtools.api.client import RBClient
import datetime
from botmanager import BotManager

class Watcher:
    """The thing that watches review board for things"""
    def __init__(self,server):
        print("The watcher is born")
        self.client = RBClient(server)
        self.names_of_interest = self.getNamesOfInterest()
        self.bot_manager = BotManager("../bots", "../bot_scripts")
        time_obj = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
        self.newest_request_seen = time_obj.isoformat()

    def getNamesOfInterest(self):
        """who the watcher should watch for"""
        "TODO make config file"
        return ['meangirl', 'zbrown', 'nobody', 'spongebob', 'cppcheck']

    def setNewestTimestamp(self,requests):
        """We want to filter requests out from the server, but need to use its timestamps"""
        """Assume chronological order he,he,he"""
        for request in requests:
            "Get timestamp from newest request in this group and inc by microsecond :)"
            time_str = request.last_updated
            time_obj = datetime.datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%SZ")
            time_obj += datetime.timedelta(1)
            self.newest_request_seen = time_obj.isoformat()
            break


    def getNewRequests(self):
        """get reviews after the timestamp"""
        print("Looking for reviews")
        root = self.client.get_root()
        requests = root.get_review_requests(last_updated_from=self.newest_request_seen)

        filtered_requests = Watcher.filterRequests(requests, self.names_of_interest)

        #Set the timestamp for next time
        self.setNewestTimestamp(requests)
        print self.newest_request_seen
        return filtered_requests

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
        while True:
            self.bot_manager.processNewReviews(self.getNewRequests())

            "TODO pick good wait time"
            time.sleep(1)

if __name__ == "__main__":
    watcher = Watcher('http://pds-rbdev01')
    watcher.watch()
