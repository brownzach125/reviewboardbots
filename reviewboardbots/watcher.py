import time
from rbtools.api.client import RBClient

class Watcher:
    'The thing that watches review board for things'
    def __init__(self,):
        print("The watcher is born")

    def getNamesOfInterest(self):
        return [ 'zbrown', 'meangirl' ]

    def getNewReviews(self):
        print("Looking for reviews")
        return []

    def watch(self):
        self.names_of_interest = self.getNamesOfInterest()

        "Until the end of time"
        print("I am watching")
        while True:
            new_reviews = self.getNewReviews()
            for review in new_reviews:
                print("I got at review")
            "TODO pick good wait time"
            time.sleep(1)


client = RBClient('http://pds-rbdev01')
root = client.get_root()
users_string = "meangirl"

date = "2010-10-1"
requests = root.get_review_requests( to_users= users_string , \
                                     time_added_from= date)
for review in requests:
    print review.summary
    difflist = review.get_diffs()
    for diff in difflist:
        diff_file_list = diff.get_file_diff_list() 


