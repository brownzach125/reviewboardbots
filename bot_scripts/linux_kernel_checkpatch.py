"""Apply the most recent linux kernel checkpatch script to diff"""
from reviewboardbots.bot import Bot
import sys, getopt, os
from subprocess import call
import pprint


class CheckPatch(Bot):
    def __init__(self, input_dir):
        if not os.path.exists(input_dir):
            raise ValueError("Check patch will go hungry if it is fed no existant food_dir")

        "Save the absolute path for later"
        self.input_dir = os.path.abspath(input_dir)

    def run(self):
        print "Run"
        request_metadata = self.getRequestMetadata()

        branch = request_metadata['branch']
        if not branch:
            "Let it be known I am cranky"
            self.reportMissingBranch()

        "Change working directory"


        "Call check patch"

    def reportMissingBranch(self):
        request_metadata = self.getRequestMetadata()
        review = self.createReview(request_metadata['id'], self.getLatestRevisionNum(), \
                                   "You need to specify the branch", False)
        self.sendReview(review)

    def getUsername(self):
        return "linux_kernel_checkpatch"

    def getPassword(self):
        return self.getUsername()

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