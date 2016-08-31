import time
from rbtools.api.client import RBClient
import datetime
from botmanager import BotManager


def parseServerTimeStamp(timestamp):
    return datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")


class Watcher:
    """The thing that watches review board for things"""
    def __init__(self,server):
        print("The watcher is born")
        self.client = RBClient(server)
        self.names_of_interest = self.getNamesOfInterest()
        self.bot_manager = BotManager("../bots", "../bot_scripts")
        self.time_obj = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
        self.newest_request_seen = self.time_obj.isoformat()
        self.requests_seen = {}

    def getNamesOfInterest(self):
        """who the watcher should watch for"""
        "TODO make config file"
        return ['meangirl', 'zbrown', 'nobody', 'spongebob']

    def setNewestTimestamp(self,requests):
        """We want to filter requests out from the server, but need to use its timestamps"""
        time_max = self.time_obj
        for request in requests:
            "Get timestamp from newest request in this group and inc by microsecond :)"
            time_str = request.last_updated
            time_obj = parseServerTimeStamp(time_str)
            #time_obj += datetime.timedelta(1)

            if time_obj.time() > time_max.time():
                time_max = time_obj

        if time_max != self.time_obj:
            self.time_obj = time_max
            self.time_obj += datetime.timedelta(seconds=1)
            print "Updating time "  + self.time_obj.isoformat()
            self.newest_request_seen = self.time_obj.isoformat()


    def getNewRequests(self):
        """get reviews after the timestamp"""
        root = self.client.get_root()
        requests = root.get_review_requests(last_updated_from=self.newest_request_seen)

        filtered_requests = self.filterRequests(requests, self.names_of_interest)

        "Set the timestamp for next time"
        self.setNewestTimestamp(requests)
        return filtered_requests

    def filterRequests(self, requests, watched_names):
        filtered_requests = {}
        for request in requests:
            for person in request.target_people:
                if person.title in watched_names and self.isNew(request):
                   if person.title not in filtered_requests:
                       filtered_requests[person.title] = []
                   filtered_requests[person.title].append(request)
        return filtered_requests

    def isNew(self, request):
        changes = self.client.get_root().get_changes(review_request_id=request.id)

        "Find the max change timestamp"
        max = parseServerTimeStamp(request.time_added)
        for change in changes:
            time_obj = parseServerTimeStamp(change.timestamp)
            if time_obj.time() > max.time():
                max = time_obj
        if request.id in self.requests_seen:
            old_time = self.requests_seen[request.id]
            if max > old_time:
                "There has been a change since we saw it last"
                self.requests_seen[request.id] = max
                return True
            else:
                return False
        else:
            self.requests_seen[request.id] = max
            return True


    def watch(self):
        """Periodically check for new reviews, spin off bots when needed"""

        "Until the end of time"
        print("I am watching")
        count = 0
        while True:
            self.bot_manager.processNewReviews(self.getNewRequests())

            count += 1
            print "Round " + str(count)
            """TODO Something is still broken here....:("""

            "TODO pick good wait time"
            time.sleep(5)

"Example"
watcher = Watcher('http://pds-rbdev01')
watcher.watch()
