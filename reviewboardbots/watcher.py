import time
from rbtools.api.client import RBClient
from botfood import BotFood
from datetime import datetime
import os

class Watcher:
    'The thing that watches review board for things'
    def __init__(self,server):
        print("The watcher is born")
        self.client = RBClient(server)
        self.names_of_interest = self.getNamesOfInterest()

    def getNamesOfInterest(self):
        'who the watcher should watch for'
        return [ 'zbrown', 'meangirl', 'nobody' ]

    def getNewReviews(self, timestamp):
        'get reviews after the timestamp'
        print("Looking for reviews")
        root = self.client.get_root()
        requests = root.get_review_requests( time_added_from=timestamp)

        'Filter requests'
        requests = Watcher.filterRequests(requests, self.names_of_interest)

        return requests

    @staticmethod
    def filterRequests(requests, watched_names):
        dict = {}
        for request in requests:
            for person in request.target_people:
                if person.title in watched_names:
                   if person.title not in dict:
                       dict[person.title] = []
                   dict[person.title].append(request)
        return dict

    def watch(self):
        'Periodically check for new reviews, spin off bots when needed'

        "Until the end of time"
        print("I am watching")
        checked_last_at = datetime.now()
        while True:
            new_reviews = self.getNewReviews(checked_last_at)
            for botname in new_reviews:
                botfood = BotFood(new_reviews[botname])
                botfood.save(os.path.join(".." , "bots" , botname))

            "TODO pick good wait time"
            time.sleep(1)

watcher = Watcher('http://pds-rbdev01')
watcher.watch()
