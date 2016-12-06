"""meangirl is not nice"""
import getopt
import sys
from random import randint

from bot import Bot

quotes = [
       "If you're from Africa, why are you white?",
       "Oh my God, Karen, you can't just ask people why they're white.",
       "Calling somebody else fat won't make you any skinnier. Calling someone stupid doesn't make you any smarter. And ruining Regina George's life definitely didn't make me any happier. All you can do in life is try to solve the problem in front of you.",
       "Gretchen, stop trying to make fetch happen! It's not going to happen!",
       "My apologies. I have a nephew named Anfernee, and I know how mad he gets when I call him Anthony. Almost as mad as I get when I think about the fact that my sister named him Anfernee.",
       "Why should Caesar just get to stomp around like a giant while the rest of us try not to get smushed under his big feet? Brutus is just as cute as Caesar, right? Brutus is just as smart as Caesar, people totally like Brutus just as much as they like Caesar, and when did it become okay for one person to be the boss of everybody because that's not what Rome is about! We should totally just STAB CAESAR!"
]


class MeanGirl(Bot):
    def run(self):
        review = self.createReview(self.get_request_metadata()['id'], self.get_latest_revision_num(), \
                                   "Your code sucks", True)
        for file_path in self.getAllFilePaths(self.get_latest_revision_path()):
            file_metadata = self.getFileMetadata(file_path)
            comment = self.create_diff_comment(file_metadata['id'], 1, 1, quotes[randint(0, len(quotes) - 1)])
            review['diff_comments'].append(comment)
        self.send_review(review)

    def get_username(self):
        return 'zbrown'

    def get_password(self):
        return ''


def main(argv):
    try:
        opts, args = getopt.getopt(argv, "i:")
    except:
        print 'meangirl.py -i <inputdir>'

    for opt, arg in opts:
        if opt == '-i':
            inputdir = arg

    bot = MeanGirl(inputdir)
    bot.run()


def do_you_care(changes):
    return Bot.do_you_care(changes)

if __name__ == "__main__":
    main(sys.argv[1:])
