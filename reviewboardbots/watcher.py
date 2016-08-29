import time

class Watcher:
    'The thing that watches review board for things'
    def __init__(self,):
        print("The watcher is born")

    def getNamesOfInterest(self):
        return [ 'zbrown', 'meangirl' ]

    def getNewReviews(self):
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
