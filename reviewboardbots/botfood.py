import os, os.path
import json
import urllib
from urlparse import urlparse, urlunparse

class BotFood:
    """It\'s what bots crave!!!"""
    def __init__(self, requestlist):
        """Make a payload out of a review list"""
        self.review_requests = []
        for review in requestlist:
            review_request = {
                'info': {
                    'id': review.id,
                },
                'diffs': BotFood.processDiffLists(review.get_diffs())
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

                fileobj = {
                    'filediff_id' : file_diff.id,
                    'name': file_diff.source_file
                }

                try:
                    fileobj['original'] = file_diff.get_original_file()._url
                except:
                    pass
                try:
                    fileobj['patched'] = file_diff.get_patched_file()._url
                except:
                    pass

                obj['files'].append(fileobj)
            result.append(obj)

        return result

    'todo, break up into more disectable chunks'
    def save(self, path):
        """Save the botfood object, including downloading the files it has urls to"""
        if not os.path.exists(path):
            os.mkdir(path)
        for request in self.review_requests:
            review_id = request['info']['id']
            reviewPath = os.path.join(path, "request" + str(review_id))
            if not os.path.exists(reviewPath):
                os.mkdir(reviewPath)

            "Make info file"
            with open(os.path.join(reviewPath, 'info'), 'w') as outfile:
                json.dump(request['info'], outfile)

            for diff in request['diffs']:
                diffpath = os.path.join(reviewPath, "revision" + str(diff['revision']) )
                if not os.path.exists(diffpath):
                    os.mkdir(diffpath)

                url = urlparse(diff['diff'])
                url = urlunparse(('http', url.netloc,\
                                 "r/" + str(review_id) + "/diff/raw/", '','',''))
                "Download and save actual diff"
                urllib.urlretrieve(url , \
                                   os.path.join(diffpath, "diff" ))

                "Download and each file\'s original and patchted version"
                for fileobj in diff['files']:
                    file_dir_name = fileobj['name'].replace("/", "_")
                    file_dir_name = file_dir_name.replace("\\" , "_")
                    file_dir_name += ".file"
                    filepath = os.path.join(diffpath,file_dir_name)
                    if not os.path.exists(filepath):
                        os.mkdir(filepath)

                    "Download original"
                    if 'original' in fileobj:
                        urllib.urlretrieve(fileobj['original'], \
                                           os.path.join(filepath, 'original'))
                    "Download patched"
                    if 'patched' in fileobj:
                        urllib.urlretrieve(fileobj['patched'], \
                                           os.path.join(filepath, 'patched'))
                    "Leave behind some metadata"
                    metadata = {
                        'name' : fileobj['name'],
                        'id'   : fileobj['filediff_id']
                    }
                    with open(os.path.join(filepath, 'metadata.json'), 'w') as outfile:
                        json.dump(metadata, outfile)