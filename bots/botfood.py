import os, os.path
import json
import urllib


class BotFood:
    """It\'s what bots crave!!!"""
    def __init__(self, requestlist):
        """Make a payload out of a review list"""
        self.review_requests = []
        for request in requestlist:
            review_request = {
                'metadata': BotFood.getRequestMetadata(request),
                'diffs': BotFood.processDiffLists(request.get_diffs())
            }
            self.review_requests.append(review_request)

    @staticmethod
    def flatten_resource(resource):
        """Have one of those nasty resources from review board, but just want all its fields?"""
        obj = {}
        for field in resource._fields:
            obj[field] = resource._fields[field]
        return obj

    @staticmethod
    def getRequestMetadata(request):
        metadata = BotFood.flatten_resource(request)
        metadata['repo'] = BotFood.getRequestRepoInfo(request)
        return metadata

    @staticmethod
    def getRequestRepoInfo(request):
        repo = request.get_repository()
        if repo:
            return BotFood.flatten_resource(repo)
        else:
            return None

    @staticmethod
    def processDiffLists(difflist):
        result = []
        for diff in difflist:
            obj = {
                'diff': diff._url,
                'resource': diff,
                'revision': diff.revision,
                'files': [],
                'metadata': BotFood.flatten_resource(diff)
            }
            diff_file_list = diff.get_files()

            for file_diff in diff_file_list:
                fileobj = {
                    'filediff_id' : file_diff.id,
                    'name': file_diff.source_file,
                    'metadata': BotFood.flatten_resource(file_diff),
                    'filediff_data': BotFood.flatten_resource(file_diff.get_diff_data())
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

    def saveRequest(self, request, path):
        if not os.path.exists(path):
            os.mkdir(path)

        "Save request metadatafile file"
        with open(os.path.join(path, 'request_metadata.json'), 'w') as outfile:
            json.dump(request['metadata'],outfile)

        for diff in request['diffs']:
            self.saveDiff(diff, os.path.join(path, "revision" + str(diff['revision'])))

        return path

    def saveDiff(self, diff, path):
        if not os.path.exists(path):
            os.mkdir(path)

        diff_content = diff['resource'].get_patch()
        with open(os.path.join(path,'diff'), 'w') as outfile:
            outfile.write(diff_content.data)

        for fileobj in diff['files']:
            file_dir_name = fileobj['name'].replace("/", "_")
            file_dir_name = file_dir_name.replace("\\" , "_")
            file_dir_name += ".file"
            self.saveFileObj(fileobj, os.path.join(path, file_dir_name))

    def saveFileObj(self, fileobj, path):
        """Save the original,patched and metadata about this fileobj"""
        if not os.path.exists(path):
            os.mkdir(path)

        "Download original"
        if 'original' in fileobj:
            urllib.urlretrieve(fileobj['original'], \
                               os.path.join(path, 'original'))
        "Download patched"
        if 'patched' in fileobj:
            urllib.urlretrieve(fileobj['patched'], \
                               os.path.join(path, 'patched'))
        "Leave behind some metadata"
        with open(os.path.join(path, 'file_metadata.json'), 'w') as outfile:
            json.dump(fileobj['metadata'], outfile)

        with open(os.path.join(path, 'filediff_metadata.json'), 'w') as outfile:
            json.dump(fileobj['filediff_data'], outfile)

    def save(self, path):
        """Save the botfood object, including downloading the files it has urls to"""

        "Create the folder to store this bot food"
        "From now on we assume it alread exists"
        #if not os.path.exists(path):
            #os.mkdir(path)

        paths = []
        for request in self.review_requests:
            paths.append(self.saveRequest(request, os.path.join(path, "request" + str(request['metadata']['id']))))
        return paths
