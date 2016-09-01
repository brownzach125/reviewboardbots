import difflib
import os
import re
import subprocess
import sys

from reviewboardbots.bot import Bot


def call_cppcheck(filename):

    #TODO: add cpplint
    cppcheck = 'cppcheck'
    return subprocess.Popen([cppcheck, "--enable=style,performance,portability", filename],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[1]

def split_line_info(line_list):
    split_lines = [x.split(':') for x in line_list]
    
    return ([x[-1] for x in split_lines], [x[:-1] for x in split_lines])

class CppCheck(Bot):
    def process_change(self, folder_path):
        metadata = self.getFileMetadata(folder_path)
        filename = metadata['name']
        file_id = metadata['id']

        old_filename = os.path.join(folder_path, 'original')
        new_filename = os.path.join(folder_path, 'patched')

        output_old = call_cppcheck(old_filename)
        output_new = call_cppcheck(new_filename)
        output_old_list, output_new_list =  output_old.split('\n'), output_new.split('\n')

        output_old_warnings, output_old_line_info = split_line_info(output_old_list)
        output_new_warnings, output_new_line_info = split_line_info(output_new_list)
        differ = difflib.Differ()
        diff_lines = differ.compare(output_old_warnings, output_new_warnings)
        print output_new_warnings
        comments = []

        #match digits at beginning of string
        digits = re.compile('(\d+)')

        for diff, line_info in zip(diff_lines, output_new_line_info):
            if diff.startswith('+'):
                print "diff: %s" % diff
                if len(line_info) > 0:
                    line_number = line_info[-1]
                else:
                    line_number = "1"

                match = re.match(digits,line_number)
                if match:
                    first_line = match.group(1)
                else:
                    first_line = 1

                comments.append({
                    "filediff_id":file_id,
                    "first_line":int(first_line),
                    "num_lines":1,
                    "text": diff[2:]
                })

        return comments

    def run(self):
        comments = []
        for file_path in self.getAllFilePaths(self.getLatestRevisionPath()):
            file_metadata = self.getFileMetadata(file_path)
            comments += self.process_change(file_path)

        ship_it = len(comments) == 0
        review = self.createReview(self.getRequestMetadata()['id'], int(self.getLatestRevisionNum()),
            "See comments" if not ship_it else "Ship it!", ship_it)
        print comments
        review['diff_comments'] += comments

        self.sendReview(review)

def main(path):
    bot = CppCheck(path, 'cppcheck', 'fpRocks')
    bot.run()

if __name__ == "__main__":
    print sys.argv
    main(sys.argv[2])