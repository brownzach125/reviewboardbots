import time
from rbtools.api.client import RBClient
import os, os.path
import json
import urllib
from urlparse import urlparse, urlunparse

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
#for review in requests:
#    print review.summary
#    difflist = review.get_diffs()
#    for diff in difflist:
#        diff_file_list = diff.get_files()
#        for file_diff in diff_file_list:
#            print(file_diff.get_self())

class BotPayLoad:
    'It\'s what bots crave!!!'
    def __init__(self, reviewlist):
        "Make a payload out of a review list"
        self.review_requests = []
        for review in reviewlist:
            review_request = {
                'info': {
                    'id': review.id,
                },
                'diffs': BotPayLoad.processDiffLists(review.get_diffs())
            }
            self.review_requests.append(review_request)

    @staticmethod
    def processDiffLists( difflist):
        result = []
        for diff in difflist:
            obj = {
               'diff': diff._url,
                'revision' : diff.revision,
                'files': []
            }
            diff_file_list = diff.get_files()
            for file_diff in diff_file_list:
                obj['file'] = {
                    'name' : file_diff.source_file,
                    'original': file_diff.get_original_file()._url,
                    'patched' : file_diff.get_patched_file()._url
                }
            result.append(obj)

        return result

    def save(self, path):
        for request in self.review_requests:
            id = request['info']['id']
            reviewPath = os.path.join(path, "request" + str(id))
            if not os.path.exists(reviewPath):
                os.mkdir(reviewPath)

            "Make info file"
            with open(os.path.join(reviewPath, 'info'), 'w') as outfile:
                json.dump(request['info'], outfile)

            for diff in request['diffs']:
                diffpath = os.path.join(reviewPath, "diff" + str(diff['revision']) )
                if not os.path.exists(diffpath):
                    os.mkdir(diffpath)

                url = urlparse(diff['diff'])
                url = urlunparse(('http', url.netloc,\
                                 "r/" + str(id) + "/diff/raw/", '','',''))
                "Download and save actual diff"
                urllib.urlretrieve(url , \
                                   os.path.join(diffpath, "diff" ))

                "Download and each file\'s original and patchted version"
                #for filename in


payload = BotPayLoad(requests)
payload.save("../bots/meangirl/")
