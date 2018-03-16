"""Apply the most recent linux kernel checkpatch script to diff"""
import os

import sh
from bot import Bot
from sh import git, cd, ls
from responseagent import Review


def branch_not_specified_message():
    message = \
                "The checkpatch bot needs the branch field of your review to contain\n" \
                "the name of your branch and your tracking branch. Set the branch field\n" \
                "to \"<branch> tracking:<tracking_branch>\" \n" \
                "\n" \
                "If you\'ve used the checkpath bot before you might expect to have to enter\n" \
                "\"<branch> tracking:origin<tracking_branch>\" The origin part of the tracking branch is no longer\n" \
                "needed and will cause an error if you include it."
    return message


def branch_does_not_exist_message(branch):
    message = \
                "The branch you specified in the branch field: {0} does not exist.\n" \
                "Check the spelling and ensure that you've pushed the branch to the ni git repo\n"
    return message.format(branch)


def tracking_branch_does_not_exist_message(tracking_branch):
    message = \
                "The tracking branch you specified in the branch field: {0} does not exist.\n" \
                "Check the spelling and ensure that it is a branch on the ni git repo\n" \
                "Also if you included 'origin' in the tracking branch name, that's no longer required and now causes errors\n" \
                "Sorry for the confusion"
    return message.format(tracking_branch)


def bio_message():
    message = \
            "Hello I'm the linux_kernel_checkpatch_bot. Thanks for adding me as a reviewer!\n" \
            "My job is to ensure all code I see follows the linux kernel coding style.\n" \
            "Here's some information about me and how to use me\n" \
            "Currently I run scripts/checkpatch.pl --strict <patch_name>\n" \
            "I need the branch field set to \"<branch name> tracking:<tracking branch name>\n" \
            "I get your code exclusively from the git repo, so in order for me to work correctly\n" \
            "make sure your code is up to date before posting any diffs to review-board, otherwise I'll just run on whatever is currently on the git repo.\n" \
            "If you do ever need me to run again, (like maybe because you posted a diff before pushing to the git repo) just change the branch field slighty.\n" \
            "For example you could just insert a space between the branch name and the word tracking.\n" \
            "\n" \
            "Now about those commits you made..."
    return message


class CheckPatch(Bot):
    def __init__(self, input_dir, config):
        Bot.__init__(self, input_dir, config)

        if not os.path.exists(input_dir):
            raise ValueError("Check patch will go hungry if it is fed no existant food_dir")
        self.input_dir = os.path.abspath(input_dir)

        self.repo_folder = os.path.join("/", "home", "zbrown", "linux2")
        self.repo_origin = "git://git.natinst.com/linux.git"

    ##############################
    # Bot overrides
    ##############################
    def bio(self):
        return bio_message()

    ##############################
    # Functions for handling git
    ##############################
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
        git.branch(["-D", "_master"])
        git.checkout(["origin/master", "-b", "_master"])
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

    ##########################################
    # Review Actions
    ##########################################
    def report_branch_problems(self, branch, tracking_branch,
                               branch_exist=True, tracking_branch_exist=True):
        request_metadata = self.get_request_metadata()
        revision_num = self.get_latest_revision_num()
        review = Review(self.get_server(), self.get_username(), self.get_password(),
                        request_metadata['id'], revision_num)

        files = self.get_all_file_paths(self.get_latest_revision_path())
        file_metadata = self.get_file_metadata(files[0])

        message = ""
        if not branch or not tracking_branch:
            message += branch_not_specified_message()
        if not branch_exist:
            message += branch_does_not_exist_message(branch)
        if not tracking_branch_exist:
            message += tracking_branch_does_not_exist_message(tracking_branch)

        comment = Review.Comment(file_id=file_metadata['id'], first_line=1,
                                 num_lines=1, message=message)
        comment.raise_issue = True

        review.comments.append(comment)
        review.ship_it = False
        review.send(self.bio())
        return

    def respond_to_patches(self, patch_details):
        request_metadata = self.get_request_metadata()

        review = Review(self.get_server(), self.get_username(), self.get_password(), request_metadata['id'],
                        self.get_latest_revision_num())

        review.ship_it = True
        #body_top
        review.header = ""

        for patch_name, patch_detail in sorted(patch_details.iteritems()):
            review.ship_it = review.ship_it and not patch_detail['failed']
            message = patch_name
            if patch_detail['failed']:
                message += ' has style problems, please review\n'
            else:
                message += ' is good to go!\n'
            review.header += message

            file_paths = self.get_all_file_paths(self.get_latest_revision_path())
            first_file_id = self.get_file_metadata(file_paths[0])['id']
            for comment in patch_detail['comments']:
                review_comment = ""
                if 'file' not in comment:
                    review_comment = Review.Comment(first_file_id, 1, 1,
                                             "In " + patch_name + ",\n" + comment['message'])
                    #review['diff_comments'].append(review_comment)
                else:
                    file_name = comment['file']
                    file_path = self.convert_real_filename_to_botfood_file_path(self.get_latest_revision_num(), file_name)
                    line_map = self.get_patched_file_line_to_unified_diff_line_map(file_path)
                    review_comment = Review.Comment(self.getFileMetadata(file_path)['id'],
                                                    line_map[int(comment['line'])], comment['num_lines'],
                                                    "In " + patch_name + ",\n" + comment['message'])

                if comment['message_type'] == "CHECK":
                    review_comment.severity = "info"
                if comment['message_type'] == "WARNING":
                    review_comment.severity = "minor"
                if comment['message_type'] == "ERROR":
                    review_comment.severity = "major"
                    review_comment.raise_issue = True
                review.comments.append(review_comment)

        review.send(self.bio())

    def check_patches(self, patches):
        obj = {}
        for patch_name in patches:
            command = sh.Command(self.repo_folder + "/linux/scripts/checkpatch.pl")
            lines = command([patch_name, "--no-color", "--strict"], _ok_code=[0, 1]).split("\n")

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

    @staticmethod
    def parse_branch_field(full_branch):
        branch = full_branch.split(' ')
        tracking_branch = None
        if not branch:
            return None, None
        branch = branch[0]

        parts = full_branch.split("tracking:")
        if len(parts) > 1:
            tracking_branch = parts[-1]
        return branch, tracking_branch

    def run(self):
        """The main execution of checkpatch bot"""
        request_metadata = self.get_request_metadata()
        full_branch = request_metadata['branch'].strip()

        branch, tracking_branch = CheckPatch.parse_branch_field(full_branch)
        if not branch or not tracking_branch:
            self.report_branch_problems(branch, tracking_branch)
            return

        self.prepare_git_folder()

        tracking_branch_exist = self.branch_exist(tracking_branch)
        branch_exist = self.branch_exist(branch)
        if not branch_exist or not tracking_branch_exist:
            self.report_branch_problems(branch, tracking_branch, branch_exist, tracking_branch_exist)
            return

        self.checkout_branch(tracking_branch)
        self.checkout_branch(branch)

        common_commit = self.find_common_commit(tracking_branch, branch)
        print common_commit

        if not common_commit:
            print "Did not find common commit"
            return

        # Find commits on branch after common commit
        commits = git(["rev-list", common_commit + ".." + branch]).rstrip().rsplit()
        print commits

        # "Format patches"
        patches = git(["format-patch", "-" + str(len(commits))]).rstrip().splitlines()

        git.checkout("_master")
        git.pull("-f")

        patch_details = self.check_patches(patches)
        self.respond_to_patches(patch_details)


#######################
# Helper functions for processing the results of scripts/checkpatch.pl
########################
def group_message_lines(lines):
    message = []
    for line in lines:
        if line == '\n' or line == "":
            yield message
            message = []
            continue
        message.append(line)


def create_comment_from_message(message):
    message_type = message[0].partition(":")[0]
    obj = {
        'message_type': message_type
    }

    second_line_break_down = []
    if len(message) > 1:
        second_line_break_down = message[1].split(":")

    is_file = False
    if len(second_line_break_down) >= 2 and second_line_break_down[1].strip() == "FILE":
        is_file = True

    if message_type in ["ERROR", "WARNING", "CHECK"]:
        if is_file:
            parse_file(message, obj)
        else:
            parse_nonfile(message, obj)

    elif message_type == "total":
        # print "Do nothing with total?"
        pass
    else:
        # print "What are you then? " + chunk_type
        pass
    if 'message' in obj:
        return obj
    else:
        return None


def parse_file(chunk, obj):
    obj['file'] = chunk[1].split(":")[2].strip()
    obj['line'] = chunk[1].split(":")[3].strip()
    obj['num_lines'] = len(chunk) - 2
    obj['message'] = obj['message_type'] + ": " + chunk[0].partition(":")[2].strip()


def parse_nonfile(chunk, obj):
    obj['message'] = obj['message_type'] + ": " + chunk[0].partition(":")[2].strip()


# Boiler Plate
def main(inputdir, config):
    CheckPatch(inputdir, config).run()


def do_you_care(changes, botname):
    return Bot.do_you_care(changes, botname)
