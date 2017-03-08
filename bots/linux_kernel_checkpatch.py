"""Apply the most recent linux kernel checkpatch script to diff"""
import os
from sh import git, cd, ls
import sh

from bots.bot import Bot


class CheckPatch(Bot):
    def __init__(self, input_dir, config):
        Bot.__init__(self, input_dir, config)

        if not os.path.exists(input_dir):
            raise ValueError("Check patch will go hungry if it is fed no existant food_dir")
        self.input_dir = os.path.abspath(input_dir)

        self.repo_folder = os.path.join("/", "home", "zbrown", "linux2")
        self.repo_origin = "git://git.natinst.com/linux.git"

    def change_to_git_folder(self):
        linux_tree_path = os.path.join(self.repo_folder, "linux")
        cd(linux_tree_path)

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
        git.clean("-fxd")
        print git.fetch("origin")
        git.checkout("master")
        git.pull("-f")
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

    def branch_exist(self, branch):
        """Does this branch exist upstream?"""
        self.change_to_git_folder()
        for line in git(["ls-remote", "--heads"], _iter=True):
            if branch == line.split("refs/heads/")[1].rstrip().strip():
                return True

    def checkout_branch(self, branch):
        self.change_to_git_folder()
        if branch in self.get_branches():
            # Maybe a better way eh?
            git.branch(["-D", branch])

        git.checkout(["-b", branch, "origin/" + branch])

    def run(self):
        """The main execution of a bot"""
        request_metadata = self.get_request_metadata()
        # branch = request_metadata['branch']
        # tracking_branch = request_metadata['tracking-branch']

        full_branch = request_metadata['branch'].strip()

        branch = None
        tracking_branch = None

        branch = full_branch.split()
        if not branch:
            self.report_missing_branch(branch, tracking_branch)
            return
        branch = branch[0]

        tracking_branch = full_branch.split("tracking:")
        if len(tracking_branch) > 1:
            tracking_branch = tracking_branch[-1]
            tracking_branch = tracking_branch.replace("origin/", "")
        else:
            tracking_branch = None

        if not branch or not tracking_branch:
            self.report_missing_branch(branch, tracking_branch)
            return

        self.prepare_git_folder()

        tracking_branch_exist = self.branch_exist(tracking_branch)
        branch_exist = self.branch_exist(branch)

        if not branch_exist or not tracking_branch_exist:
            self.report_missing_branch_exist(branch, branch_exist, tracking_branch, tracking_branch_exist)
            return

        self.checkout_branch(tracking_branch)
        self.checkout_branch(branch)

        common_commit = self.find_common_commit(tracking_branch, branch)
        print common_commit

        if not common_commit:
            print "Did not find common commit"
            return

        #Find commits on branch after common commit
        commits = git(["rev-list", common_commit + ".." + branch]).rstrip().rsplit()
        print commits

        #"Format patches"
        patches = git(["format-patch", "-" + str(len(commits))]).rstrip().splitlines()

        self.checkout_branch("master")

        patch_details = self.check_patches(patches)
        self.respond_to_patches(patch_details)

    def report_missing_branch(self, branch, tracking_branch):
        request_metadata = self.get_request_metadata()
        revision_num = self.get_latest_revision_num()
        review = self.create_review(request_metadata['id'], revision_num, \
                                   "There are issues", False)

        files = self.getAllFilePaths(self.get_latest_revision_path())
        file_metadata = self.getFileMetadata(files[0])

        if not branch or not tracking_branch:
            message = "Please specify the branch and tracking branch.\n" \
                      "<branch> tracking:<tracking_branch>"
        comment = self.create_diff_comment(filediff_id=file_metadata['id'], first_line=1,
                                           num_lines=1, text=message)
        comment['issue_opened'] = True

        review['diff_comments'].append(comment)
        self.send_review(review)

    def report_missing_branch_exist(self, branch, branch_exist, tracking_branch, tracking_branch_exist):
        request_metadata = self.get_request_metadata()
        revision_num = self.get_latest_revision_num()
        review = self.create_review(request_metadata['id'], revision_num, \
                                   "There are issues", False)

        files = self.getAllFilePaths(self.get_latest_revision_path())
        file_metadata = self.getFileMetadata(files[0])

        message = ""
        if not branch_exist:
            message += "Branch: " + branch + " does not exist\n"
        if not tracking_branch_exist:
            message += "Tracking-Branch: " + tracking_branch + " does not exist\n"

        comment = self.create_diff_comment(filediff_id=file_metadata['id'], first_line=1,
                                           num_lines=1, text=message)
        comment['issue_opened'] = True

        review['diff_comments'].append(comment)
        self.send_review(review)

    def respond_to_patches(self, patch_details):
        request_metadata = self.get_request_metadata()
        review = self.create_review(request_id=request_metadata['id'], revision_id=self.get_latest_revision_num())
        review['ship_it'] = True
        review['body_top'] = ""

        for patch_name, patch_detail in sorted(patch_details.iteritems()):
            review['ship_it'] = review['ship_it'] and not patch_detail['failed']
            message = patch_name
            if patch_detail['failed']:
                message += ' has style problems, please review\n'
            else:
                message += ' is good to go!\n'
            review['body_top'] += message

            file_paths = self.getAllFilePaths(self.get_latest_revision_path())
            first_file_id = self.getFileMetadata(file_paths[0])['id']
            for comment in patch_detail['comments']:
                if 'file' not in comment:
                    review_comment = self.create_diff_comment(first_file_id, 1, 1,
                                                              "In " + patch_name + ",\n" + comment['message'])
                    review_comment['issue_opened'] = True
                    review['diff_comments'].append(review_comment)
                else:
                    file_name = comment['file']
                    file_path = self.convertRealFilenametoBotFoodFilePath(self.get_latest_revision_num(), file_name)
                    line_map = self.getPatchedFileLineToUnifiedDiffLineMap(file_path)
                    review_comment = self.create_diff_comment(self.getFileMetadata(file_path)['id'],
                                                              line_map[int(comment['line'])], comment['num_lines'],
                                                              "In " + patch_name + ",\n" + comment['message'])
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
        if line == '\n' or line == "":
            yield message
            message = []
            continue
        message.append(line)


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


# Boiler Plate
def main(inputdir, config):
    CheckPatch(inputdir, config).run()


def do_you_care(changes, botname):
    return Bot.do_you_care(changes, botname)

