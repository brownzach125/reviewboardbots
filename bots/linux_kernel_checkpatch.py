"""Apply the most recent linux kernel checkpatch script to diff"""
import getopt
import os
import subprocess
import sys
from subprocess import check_output, call
from sh import git, cd, ls
import sh

from bots.bot import Bot


class CheckPatch(Bot):
    def __init__(self, input_dir):
        if not os.path.exists(input_dir):
            raise ValueError("Check patch will go hungry if it is fed no existant food_dir")
        self.input_dir = os.path.abspath(input_dir)

        self.repo_folder = os.path.join("/", "home", "zbrown", "linux2")
        self.repo_origin = "git://git.natinst.com/linux.git"

    def change_to_git_folder(self):
        "My path"
        linux_tree_path = os.path.join(self.repo_folder, "linux")
        "Change working directory"
        cd(linux_tree_path)

    @staticmethod
    def process_output(line):
        print line

    def prepare_git_folder(self):
        # Does the repo exist?
        print "-------------Preparing git folder"
        if "linux" not in ls(os.path.join(self.repo_folder)).split():
            print "linux dir does not exist, cloning now"
            cd(self.repo_folder)
            for line in git.clone(self.repo_origin):
                print line
            print "Cloning successful"

        self.change_to_git_folder()
        print git.fetch("origin")
        git.checkout("master")
        print "-------------Finished preparing git folder"

    def find_common_commit(self, a, b):
        self.change_to_git_folder()
        print "--------------Finding common commit"
        common_commit = git(["merge-base", a, b]).rstrip()
        return common_commit

    def get_branches(self):
        # TODO handle errors
        self.change_to_git_folder()
        branches = []
        for line in git.branch("--no-color", _iter=True):
            branches.append(line.rstrip().split()[-1])
        return branches

    def checkout_branch(self, branch):
        self.change_to_git_folder()
        if branch in self.get_branches():
            # Maybe a better way eh?
            git.branch(["-D", branch])

        git.checkout(["-b", branch, "origin/" + branch])

    def switch_to_branch(self, branch):
        # TODO handle errors
        self.change_to_git_folder()
        if branch in self.get_branches():
            git.checkout(branch)
        else:
            raise "That branch no exist"

    def run(self):
        """The main execution of a bot"""
        request_metadata = self.get_request_metadata()
        branch = request_metadata['branch']
        tracking_branch = request_metadata['tracking-branch']
        if not branch or not tracking_branch:
            self.report_missing_branch(branch, tracking_branch)

        self.prepare_git_folder()

        self.checkout_branch(branch)
        self.checkout_branch(tracking_branch)

        self.switch_to_branch(branch)

        common_commit = self.find_common_commit(tracking_branch, branch)
        print common_commit

        if not common_commit:
            print "Did not find common commit"
            return

        self.switch_to_branch(branch)

        #Find commits on branch after common commit
        commits = git(["rev-list", common_commit + ".." + branch]).rstrip().rsplit()
        print commits

        #"Format patches"
        patches = git(["format-patch", "-" + str(len(commits))]).rstrip().splitlines()

        patch_details = self.check_patches(patches)
        self.respond_to_patches(patch_details)

    def report_missing_branch(self):
        # TODO handle input of branch and tracking branch
        # i.e determine which are null and reprot
        request_metadata = self.get_request_metadata()
        revision_num = self.get_latest_revision_num()
        review = self.createReview(request_metadata['id'], revision_num, \
                                   "There are issues", False)

        files = self.getAllFilePaths(self.get_latest_revision_path())
        file_metadata = self.getFileMetadata(files[0])
        comment = self.createDiffComment(filediff_id=file_metadata['id'], first_line=1,
                                         num_lines=1,text="Please specify the branch!")
        comment['issue_opened'] = True

        review['diff_comments'].append(comment)
        self.send_review(review)

    def get_username(self):
        return "linux_kernel_checkpatch"

    def get_password(self):
        return self.get_username()

    def respond_to_patches(self, patch_details):
        request_metadata = self.get_request_metadata()
        for patch_name in patch_details:
            patch_detail = patch_details[patch_name]
            review = self.createReview(request_id=request_metadata['id'], revision_id=self.get_latest_revision_num())
            review['ship_it'] = not patch_detail['failed']
            message = patch_name
            if patch_detail['failed']:
                message += ' has style problems, please review'
            else:
                message += ' is good to go!'
            review['body_top'] = message

            file_paths = self.getAllFilePaths(self.get_latest_revision_path())
            first_file_id = self.getFileMetadata(file_paths[0])['id']
            for comment in patch_detail['comments']:
                if 'file' not in comment:
                    review_comment=self.createDiffComment(first_file_id,1,1,comment['message'])
                    review_comment['issue_opened'] = True
                    review['diff_comments'].append(review_comment)
                else:
                    file_name = comment['file']
                    file_path = self.convertRealFilenametoBotFoodFilePath(self.get_latest_revision_num(), file_name)
                    line_map = self.getPatchedFileLineToUnifiedDiffLineMap(file_path)
                    review_comment = self.createDiffComment(self.getFileMetadata(file_path)['id'],
                                                            line_map[int(comment['line'])], comment['num_lines'],
                                                            comment['message'])
                    review_comment['issue_opened'] = True
                    review['diff_comments'].append(review_comment)

            self.send_review(review)

    def check_patches(self, patches):
        obj = {}
        for patch_name in patches:
            command = sh.Command(self.repo_folder + "/linux/scripts/checkpatch.pl")
            lines = command([patch_name, "--no-color"], _ok_code=[0, 1]).split("\n")

            messages = list(group_message_lines(lines))
            comments = []
            for message in messages:
                comment = create_comment_from_message(message)
                if comment:
                    comments.append(comment)

            obj[patch_name] = {
                "comments": comments,
                "failed": len(comments),
                "name": patch_name
            }

        return obj


def group_message_lines(lines):
    message = []
    for line in lines:
        if line == '\n':
            yield message
            message = []
        message.append(line)
    yield message


def create_comment_from_message(message):
    chunk = parse_chunk(message)
    if 'message' in chunk:
        return chunk
    else:
        return None


def parse_chunk(chunk):
    chunk_type = chunk[0].partition(":")[0]
    obj = {
        'chunk_type':chunk_type
    }

    if len(chunk) > 1:
        second_line_break_down = chunk[1].split(":")
    else:
        second_line_break_down = []

    is_file = False
    if len(second_line_break_down) >= 2 and second_line_break_down[1].strip() == "FILE":
        is_file = True

    if chunk_type == "ERROR" or chunk_type == "WARNING":
        if is_file:
            parse_file(chunk, obj)
        else:
            parse_nonfile(chunk, obj)

    elif chunk_type == "total":
        #print "Do nothing with total?"
        pass
    else:
        #print "What are you then? " + chunk_type
        pass

    return obj


def parse_file(chunk, obj):
    obj['file'] = chunk[1].split(":")[2].strip()
    obj['line'] = chunk[1].split(":")[3].strip()
    obj['num_lines'] = len(chunk) - 2
    obj['message'] = obj['chunk_type'] + ": " + chunk[0].partition(":")[2].strip()


def parse_nonfile(chunk, obj):
    obj['message'] = obj['chunk_type'] + ": " + chunk[0].partition(":")[2].strip()


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