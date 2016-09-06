"""Apply the most recent linux kernel checkpatch script to diff"""
from reviewboardbots.bot import Bot
import sys, getopt, os
from subprocess import check_output, call
import subprocess

class CheckPatch(Bot):
    def changeToGitFolder(self):
        "My path"
        linux_tree_path = os.path.join("/", "home", "zbrown", "linux2","linux")
        "Change working directory"
        os.chdir(linux_tree_path)

    def prepareGitFolder(self):
        self.changeToGitFolder()
        print "-------------Preparing git folder"
        call(['git','fetch'])
        call(['git','checkout','master'])
        call(['git','branch','-D','nilrt/16.0/4.1'])
        call(['git','checkout', '-b', 'nilrt/16.0/4.1','origin/nilrt/16.0/4.1'])
        call(['git','branch','-D','dev/zbrown/sdhci-upstream'])
        call(['git','checkout', '-b', 'dev/zbrown/sdhci-upstream','origin/dev/zbrown/sdhci-upstream'])
        call(['git','checkout','master'])
        print "-------------Finished preparing git folder"

    def deleteBranch(self, branch):
        print "------------Deleting branch " + branch
        branches = check_output(['git','branch']).rstrip().rsplit()
        if branch in branches:
            call(['git', 'branch','-D', branch])
        print "------------Branch deleted if it existed"

    def __init__(self, input_dir):
        if not os.path.exists(input_dir):
            raise ValueError("Check patch will go hungry if it is fed no existant food_dir")
        self.input_dir = os.path.abspath(input_dir)

    def checkoutBranchFromRemote(self, branch):
        call(['git','checkout','-b', branch, 'origin/' + branch])
        return True

    def findBaseBranch(self, branch):
        print "------------Finding base Branch"
        if self.checkoutBranchFromRemote(branch):
            magic_command_str=  \
                'git show-branch | sed "s/].*//" | grep "\*" | grep -v "$(git rev-parse --abbrev-ref HEAD)" | head -n1 | sed "s/^.*\[//" > output.txt'
            call(magic_command_str, shell=True)
            with open('output.txt') as datafile:
                print "------------Found base branch"
                base_branch = datafile.readline()
                os.unlink('output.txt')
                return base_branch.rstrip()
        else:
            return None

    def cleanUpGitFolder(self):
        print "Make clean up function"

    def findCommonCommit(self, A, B):
        try:
            print "--------------Findind common commit"
            common_commit = check_output(['git', 'merge-base', A, B]).rstrip()
            print "Found common commit"
            return common_commit
        except subprocess.CalledProcessError as error:
            print "--------------Find common commit failed"
            print error
            return None

    def run(self):
        request_metadata = self.getRequestMetadata()
        branch = request_metadata['branch']
        if not branch:
            self.reportMissingBranch()
            return

        self.prepareGitFolder()

        self.deleteBranch(branch)

        base_branch = self.findBaseBranch(branch)

        if not base_branch:
            print "Did not find base branch"
            return self.cleanUpGitFolder()

        common_commit = self.findCommonCommit(base_branch,branch)

        if not common_commit:
            print "Did not find commont commit"
            return

        call(['git', 'checkout', branch])

        "Find commits on branch after common commit"
        commits = check_output(['git', 'rev-list', common_commit+".." + branch]).rstrip().rsplit()

        "Format patches"
        patches= check_output(['git', 'format-patch', '-' + str(len(commits))]).rstrip().splitlines()

        patch_details = checkPatches(patches)
        self.respondToPatches(patch_details)

    def reportMissingBranch(self):
        request_metadata = self.getRequestMetadata()
        revision_num = self.getLatestRevisionNum()
        review = self.createReview(request_metadata['id'], revision_num, \
                                   "There are issues", False)

        files = self.getAllFilePaths(self.getLatestRevisionPath())
        file_metadata = self.getFileMetadata(files[0])
        comment = self.createDiffComment(filediff_id=file_metadata['id'], first_line=1,
                                         num_lines=1,text="Please specify the branch!")
        comment['issue_opened'] = True

        review['diff_comments'].append(comment)
        self.sendReview(review)

    def getUsername(self):
        return "linux_kernel_checkpatch"

    def getPassword(self):
        return self.getUsername()

    def respondToPatches(self, patch_details):
        request_metadata = self.getRequestMetadata()
        for patch_name in patch_details:
            patch_detail = patch_details[patch_name]
            review = self.createReview(request_id=request_metadata['id'],revision_id=self.getLatestRevisionNum())
            review['ship_it'] = not patch_detail['failed']
            message = patch_name
            if patch_detail['failed']:
                message += ' has style problems, please review'
            else:
                message += ' is good to go!'
            review['body_top'] = message

            file_paths = self.getAllFilePaths(self.getLatestRevisionPath())
            first_file_id = self.getFileMetadata(file_paths[0])['id']
            for comment in patch_detail['comments']:
                if 'file' not in comment:
                    review_comment=self.createDiffComment(first_file_id,1,1,comment['message'])
                    review_comment['issue_opened'] = True
                    review['diff_comments'].append(review_comment)
                else:
                    file_name = comment['file']
                    file_path = self.convertRealFilenametoBotFoodFilePath(self.getLatestRevisionNum(),file_name)
                    line_map = self.getPatchedFileLineToUnifiedDiffLineMap(file_path)
                    review_comment=self.createDiffComment(self.getFileMetadata(file_path)['id'],
                                                          line_map[int(comment['line'])],comment['num_lines'], comment['message'])
                    review_comment['issue_opened'] = True
                    review['diff_comments'].append(review_comment)

            self.sendReview(review)


def checkPatches(patches):
    obj = {}
    for patch_name in patches:
        command_str = "scripts/checkpatch.pl " + patch_name + ' > ' + patch_name + ".txt"
        call([command_str], shell=True)
        lines = None
        with open(patch_name + '.txt', 'r') as data_file:
            lines = data_file.readlines()

        chunks = parseLinesIntoMessageChunks(lines)
        comments = []
        for chunk in chunks:
            comment = processChunk(chunk)
            if comment:
                comments.append(comment)

        obj[patch_name] = {
            "comments": comments,
            "failed": len(comments),
            "name": patch_name
        }

    return obj

def processChunk(chunk):
    chunk = parseChunk(chunk)
    if 'message' in chunk:
        return chunk
    else:
        return None

def parseChunk(chunk):
    type = chunk[0].partition(":")[0]
    obj = {
        'type':type
    }

    if len(chunk) > 1:
        second_line_break_down = chunk[1].split(":")
    else:
        second_line_break_down = []

    isFile = False
    if len(second_line_break_down) >= 2 and second_line_break_down[1].strip() == "FILE":
        isFile = True

    if (type == "ERROR" or type == "WARNING"):
        if isFile:
            parseFile(chunk, obj)
        else:
            parseNonFile(chunk, obj)

    elif (type == "total"):
        #print "Do nothing with total?"
        pass
    else:
        #print "What are you then? " + type
        pass

    return obj

def parseFile(chunk, obj):
    obj['file'] = chunk[1].split(":")[2].strip()
    obj['line'] = chunk[1].split(":")[3].strip()
    obj['num_lines'] = len(chunk) - 2
    obj['message'] = obj['type'] + ": " + chunk[0].partition(":")[2].strip()

def parseNonFile(chunk,obj):
    obj['message'] = obj['type'] + ": " + chunk[0].partition(":")[2].strip()

def parseLinesIntoMessageChunks(lines):
  chunks = []
  chunk =[]
  for line in lines:
    if line == '\n':
        chunks.append(chunk)
        chunk = []
    else:
        chunk.append(line)
  return chunks



def main(argv):
    try:
        opts, args = getopt.getopt(argv, "i:")
    except:
        print 'checkpatch.py -i <inputdir>'

    for opt, arg in opts:
        if opt == '-i':
            inputdir = arg

    bot = CheckPatch(inputdir)
    bot.run()

if __name__ == "__main__":
    main(sys.argv[1:])