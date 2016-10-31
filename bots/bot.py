"""
* Assume each bot has just one review_request to deal with
* Parent class of all bots, it has a lot of nice helpers to manage the
* file structure created by botfood, though I guess long run I should make
* botfood work both ways..., but in any event there are helper functions
* in the class that children classes will benefit from.
"""
import os, sys
import json
from reviewboardbots.responseagent import ResponseAgent


class Bot:
    """Generic bot with helper functions"""
    def __init__(self, input_dir, username="username", password="password"):
        "Save the absolute path for later"
        self.input_dir = os.path.abspath(input_dir)
        self._username = username
        self._password = password

    def __del__(self):
        """Consume the input folder"""
        #os.unlink(self.input_dir)

    def getRequestMetadata(self):
        with open(os.path.join(self.input_dir, 'request_metadata.json')) as data_file:
            return json.load(data_file)

    def getRevisionPath(self, number):
        """revision"""
        return os.path.join(self.input_dir, 'revision' + str(number))

    def getLatestRevisionNum(self):
        max = 0
        for folder in os.listdir(self.input_dir):
            if 'revision' in folder:
                revision_num = folder[len('revision'):]
                if max < revision_num:
                    max = revision_num
        return max

    def getLatestRevisionPath(self):
        max = 0
        foldername = ""
        for folder in os.listdir(self.input_dir):
            if 'revision' in folder:
                revision_num = folder[len('revision'):]
                if max < revision_num:
                    foldername = folder
                    max = revision_num

        return os.path.join(self.input_dir, foldername)

    def getDiffPath(self, revisionPath):
        return os.path.join(revisionPath, "diff")

    def getAllFilePaths(self, revisionPath):
        li = os.listdir(revisionPath)
        li = [ os.path.join(revisionPath, elem) for elem in li]
        return [ elem for elem in li if os.path.isdir(elem) ]

    def getFileMetadata(self, filepath):
        with open(os.path.join(filepath, 'file_metadata.json')) as data_file:
            return json.load(data_file)

    def getRevisionMetadata(self, revisionpath):
        with open(os.path.join(revisionpath, 'revision_metadata.json')) as data_file:
            return json.load(data_file)

    def getFileDiffObj(self, filepath):
        with open(os.path.join(filepath, 'filediff_metadata.json')) as data_file:
            return json.load(data_file)

    def run(self):
        """Process the input"""
        print "I don\'t do anything"

    def createReview(self, request_id, revision_id=1, message="Default bot review message", ship_it=False):
        """Creates the bareminimum review, feel free to add more once you have it"""
        return {
            'request_id': request_id,
            'revision_id': revision_id,
            'diff_comments':[],
            'general_comments':[],
            'body_top': message ,
            'ship_it': ship_it,
            'public': True
        }

    def createDiffComment(self, filediff_id, first_line, num_lines, text):
        """Creates the bare minium diff comment, feel free to add more once you have it"""
        return {
            'filediff_id':filediff_id,
            'first_line':first_line,
            'num_lines':num_lines,
            'text':text
        }

    def createGeneralComment(self, text):
        """Creates the bare minimum comment, feel free to add more once you have it"""
        return {
            'text':text
        }

    def getUsername(self):
        return self._username

    def getPassword(self):
        return self._password

    def getServer(self):
        return 'http://pds-rbdev01'

    def sendReview(self, review):
        agent = ResponseAgent(self.getServer(), self.getUsername(), self.getPassword())
        agent.respond(review)

    def convertRealFilenametoBotFoodFilePath(self, revision_id, filename):
        diff_path = self.getRevisionPath(revision_id)
        file_path = filename.replace("/", "_")
        file_path = file_path.replace("\\" , "_")
        file_path += ".file"
        return os.path.join(diff_path, file_path)

    def getPatchedFileLineToUnifiedDiffLineMap(self, file_path):
        metadata = self.getFileMetadata(file_path)
        file_id = metadata['id']
        diff_metadata = self.getFileDiffObj(file_path)

        # Compute mappings from lines in the new file to lines
        # in the overall diff (so we can report accurate line
        # numbers when writing comments.)
        new_line_to_diff_line = {}
        for chunk in diff_metadata['chunks']:
            for chunk_line in chunk['lines']:
                diff_line = chunk_line[0]
                new_line = chunk_line[4]
                if not new_line:
                    continue
                if new_line in new_line_to_diff_line:
                    print "Error creating diff metadata: line numbers may be off"
                new_line_to_diff_line[new_line] = diff_line
        return new_line_to_diff_line

