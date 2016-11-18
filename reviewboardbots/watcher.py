import time
from rbtools.api.client import RBClient
import datetime
from tinydb import TinyDB, Query


def parseServerTimeStamp(timestamp):
    return datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")


class Data:
    def __init__(self):
        self.db = TinyDB('db.json')
        self.db.table('requests')


class Watcher:
    """The thing that watches review board for things"""
    def __init__(self, server, bot_manager, bot_name_list):
        self.data = Data()
        print("The watcher is born")
        self.client = RBClient(server)

        self.bot_name_list = bot_name_list
        self.names_of_interest = self.get_names_of_interest()

        self.bot_manager = bot_manager
        self.time_obj = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
        self.newest_request_seen_timestamp = self.time_obj.isoformat()
        self.requests_seen = {}

    def get_names_of_interest(self):
        """who the watcher should watch for"""
        return self.bot_name_list

    def set_newest_timestamp(self, requests):
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
            self.newest_request_seen_timestamp = self.time_obj.isoformat()

    def get_new_requests(self):
        """get reviews after the timestamp"""
        root = self.client.get_root()
        requests = root.get_review_requests(last_updated_from=self.newest_request_seen_timestamp)

        filtered_requests = self.filter_requests(requests, self.names_of_interest)

        #Set the timestamp for next time
        self.set_newest_timestamp(requests)
        return filtered_requests

    def filter_requests(self, requests, watched_names):
        filtered_requests = {}
        for request in requests:
            for person in request.target_people:
                if person.title in watched_names and self.isNew(request):
                   if person.title not in filtered_requests:
                       filtered_requests[person.title] = []
                   filtered_requests[person.title].append(request)
        return filtered_requests

    def is_new(self, request):
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
        self.keep_watching = True

        "Until my watch is ended"
        print("Watcher: I am watching")
        count = 0
        while self.keep_watching:
            self.bot_manager.process_new_requests(self.get_new_requests())

            count += 1
            print "Round " + str(count)
            """TODO Something is still broken here....:("""
            "TODO pick good wait time"
            time.sleep(5)

        print("Watcher: My watch has ended")

    def stop(self):
        self.keep_watching = False

data = Data()
