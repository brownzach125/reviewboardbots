"""Apply the most recent linux kernel checkpatch script to diff"""
import os
import sh
from sh import pep8, cp, mkdir, cat

from bots.bot import Bot

peppy_bio_message = "Hi I'm pylint_bot, but you can call me Peppy.\n" \
                    "I run pep8 on all the python file changes in your diff, so I should only report issues your code introduced.\n" \
                    "I'll respond any time you change your diff. \n" \
                    "Remember pep8 is just a script and I'm just a bot (not to mention I'm in early beta).\n" \
                    "Trust your instincts."
branch_field_not_set_message = "You forgot to set the branch field.\n" \
                               "It won't affect me, but I figured I'd say something"
diff_is_good_message = "Everything's A-OK."
diff_has_problems = "There are some pep8 issues with your diff.\n" \
                    "I'm not too crazy about those guys."


def call_pep8(metadata, diff_filepath, patched_filepath):
    try:
        if os.path.isfile(diff_filepath):
            os.chdir(os.path.join("/", "home", "zbrown", "temp"))
            folder, _ = os.path.split(metadata["dest_file"])
            if folder:
                folder = folder.replace("//", "")
                mkdir(folder, "-p")
            temp_path = metadata["dest_file"].replace("//", "")
            cp(patched_filepath, temp_path)

            lines = []
            with open(diff_filepath, 'r') as oldfile:
                lines = oldfile.readlines()
            lines[0] = lines[0].replace("//", "")
            lines[1] = lines[1].replace("//", "")
            with open(diff_filepath, 'w') as newfile:
                newfile.writelines(lines)

            mypep8 = pep8.bake("--diff")
            mypep8(cat(diff_filepath))

    except sh.ErrorReturnCode_1 as error:
        output = error.stdout.rstrip()
        lines = output.split("\n")
        result = []
        for line in lines:
            parts = line.split(":")
            issue = {
                "message": parts[3],
                "filename": metadata["dest_file"],
                "line": parts[1],
                "col": parts[2]
            }
            result.append(issue)
        return result
    except Exception as error:
        print "HI"
        print error
    return []


class Peppy(Bot):
    """Runs python linter pep8"""
    def __init__(self, input_dir, config):
        Bot.__init__(self, input_dir, config)

        if not os.path.exists(input_dir):
            raise ValueError("Peppy needs his carrots, give him a real food_dir")
        self.input_dir = os.path.abspath(input_dir)

    def bio(self):
        return peppy_bio_message

    def run(self):
        """The main execution of a bot"""
        request_metadata = self.get_request_metadata()
        branch = request_metadata['branch'].strip()
        #if not branch:
            #self.report_missing_branch()
            # Peppy does not care if you branch is not set

        issues = self.run_pep8()
        self.respond(issues)

    def report_missing_branch(self):
        request_metadata = self.get_request_metadata()
        revision_num = self.get_latest_revision_num()
        review = self.create_review(request_metadata['id'], revision_num, \
                                    "There are issues", False)

        files = self.get_all_file_paths(self.get_latest_revision_path())
        file_metadata = self.get_file_metadata(files[0])

        comment = self.create_diff_comment(filediff_id=file_metadata['id'],
                                           first_line=1,
                                           num_lines=1,
                                           text=peppy_bio_message)
        comment['issue_opened'] = True

        review['diff_comments'].append(comment)
        self.send_review(review)

    def respond(self, issues):
        request_metadata = self.get_request_metadata()
        review = self.create_review(request_id=request_metadata['id'],
                                    revision_id=self.get_latest_revision_num())
        review['ship_it'] = not len(issues)
        review['body_top'] = diff_is_good_message

        for issue in issues:
            review['body_top'] = diff_has_problems
            file_name = issue["filename"]
            file_path = self.convertRealFilenametoBotFoodFilePath(self.get_latest_revision_num(), file_name)
            line_map = self.get_patched_file_line_to_unified_diff_line_map(file_path)
            review_comment = self.create_diff_comment(self.get_file_metadata(file_path)['id'],
                                                      line_map[int(issue['line'])],
                                                      1,
                                                      issue['message'])
            review_comment['issue_opened'] = True
            review['diff_comments'].append(review_comment)

        self.send_review(review)

    def process_change(self, filename, file_path):
        metadata = self.get_file_metadata(file_path)

        diff_filename = os.path.join(file_path, 'diff')
        patched_filename = os.path.join(file_path, 'patched')
        return call_pep8(metadata, diff_filename, patched_filename)

    def run_pep8(self):
        result = []
        for file_path in self.get_all_file_paths(self.get_latest_revision_path()):
            file_metadata = self.get_file_metadata(file_path)
            # Ignore non python files
            source_file = file_metadata['dest_file']
            filename, file_extension = os.path.splitext(source_file)
            if file_extension != ".py":
                continue

            # Process this python file
            result += self.process_change(filename, file_path)
        return result

    @staticmethod
    def do_you_care(changes, botname):
        # Peppy doesn't really care about branch names
        for change in changes:
            fields_changed = change['fields_changed']
            if 'diff' in fields_changed:
                return True

            if 'target_people' in fields_changed and 'added' in fields_changed['target_people']:
                for added_person in fields_changed['target_people']['added']:
                    if added_person['username'] == botname:
                        return True

        return False


# Boiler Plate
def main(inputdir, config):
    Peppy(inputdir, config).run()


def do_you_care(changes, botname):
    return Peppy.do_you_care(changes, botname)


#value = call_pep8("test1.py", '/home/zbrown/techWeek/reviewboardbots/botfood/177905/revision1/test1.py.file/patched')
#print value
