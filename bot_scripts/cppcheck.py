import difflib
import os
import re
import subprocess
import sys

from reviewboardbots.bot import Bot



#2 = first line #
#5 = second line # (optional)
#6 - Description
CPPCHECK_PARSE = re.compile(r'^\[([^\]]*:(\d+))\](\s*->\s*\[([^\]]*:(\d+))\])?:\s*(.*)$')

def call_cppcheck(filename):

    #TODO: add cpplint
    cppcheck = 'cppcheck'
    return subprocess.Popen([cppcheck, "--enable=style,performance,portability", filename],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()[1]

def split_line_info(line_list):
    
    warnings = []
    start_lines = []
    line_lens = []

    for line in line_list:
        print 'line: %s' % line
        if line != '':
            match = re.match(CPPCHECK_PARSE,line)
            start_line = int(match.group(2))
            
            if match.group(5):
                end_line = int(match.group(5))
                line_len = end_line - start_line
            else:
                line_len = 1

            warnings.append(match.group(6))
            start_lines.append(start_line)
            line_lens.append(line_len)
            
    return warnings, start_lines, line_lens

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

        output_old_warnings = split_line_info(output_old_list)[0]
        output_new_warnings, output_line_starts, output_line_ends = split_line_info(output_new_list)

        differ = difflib.Differ()
        diff_lines = differ.compare(output_old_warnings, output_new_warnings)
        comments = []

        #match digits at beginning of string
        digits = re.compile('(\d+)')

        for diff, line_start, line_end in zip(diff_lines, output_line_starts, output_line_ends):
            if diff.startswith('+'):
                comments.append({
                    "filediff_id":file_id,
                    "first_line":line_start,
                    "num_lines":line_end,
                    "text": diff[2:]
                })

        return comments

    def run(self):
        comments = []
        for file_path in self.getAllFilePaths(self.getLatestRevisionPath()):
            file_metadata = self.getFileMetadata(file_path)
            comments += self.process_change(file_path)

        ship_it = len(comments) == 0
        review = self.createReview(self.getReviewMetadata()['id'], int(self.getLatestRevisionNum()),
            "See comments" if not ship_it else "Ship it!", ship_it)
        review['comments'] += comments

        self.sendReview(review)

def main(path):
    bot = CppCheck(path, 'cppcheck', 'fpRocks')
    bot.run()

if __name__ == "__main__":
    print sys.argv
    main(sys.argv[2])