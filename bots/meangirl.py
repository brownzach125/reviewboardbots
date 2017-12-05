"""meangirl is not nice

   This bot is meant to be an example.
   It hopes to simple enough to be understood, but show off enough of the frameworks functions to
   help bot authors write their bots.
"""
from random import randint
from bot import Bot
from responseagent import Review

"""
    The meangirl bot does nothing but post meangirl quotes as reviews.
"""
quotes = [
       "If you're from Africa, why are you white?",
       "Oh my God, Karen, you can't just ask people why they're white.",
       "Calling somebody else fat won't make you any skinnier. Calling someone stupid doesn't make you any smarter. And ruining Regina George's life definitely didn't make me any happier. All you can do in life is try to solve the problem in front of you.",
       "Gretchen, stop trying to make fetch happen! It's not going to happen!",
       "My apologies. I have a nephew named Anfernee, and I know how mad he gets when I call him Anthony. Almost as mad as I get when I think about the fact that my sister named him Anfernee.",
       "Why should Caesar just get to stomp around like a giant while the rest of us try not to get smushed under his big feet? Brutus is just as cute as Caesar, right? Brutus is just as smart as Caesar, people totally like Brutus just as much as they like Caesar, and when did it become okay for one person to be the boss of everybody because that's not what Rome is about! We should totally just STAB CAESAR!"
]


# Every bot should extend the Bot class.
class MeanGirl(Bot):
    # An instance of Meangirl will be created by the BotManager each time
    # a review request needs attention by meangirl
    def __init(self, input_dir, config):
        Bot.__init__(self, input_dir, config)

    # A helper function, tell the world about your self bot.
    def bio(self):
        return "I am meangirl"

    # The run function is the meat of every bot
    # it is what the BotManager will call after creating the bot
    def run(self):
        # The metadata of the request object contains interesting things about the request i.e branch and description
        request_metadata = self.get_request_metadata()
        # To post reviews you need to specify which revision number
        # you'll usually want the latest one, but I'm not going to tell you what to do.
        revision_num = self.get_latest_revision_num()

        # Create a review object.
        review = Review(self.get_server(), self.get_username(), self.get_password(),
                        request_metadata['id'], revision_num)

        # This is general reply the bot will give
        review.header = "Your code sucks."

        # Mean girl wants to comment on every file that changed in this revision
        # So she iterates over all the file_paths
        for file_path in self.get_all_file_paths(self.get_latest_revision_path()):
            # To make a comment on a particular file you need it's metadata
            file_metadata = self.get_file_metadata(file_path)

            random_mean_girl_quote = quotes[randint(0, len(quotes) -1)]
            # This is the comment on an actual file,
            # you specify the file, the line where the issue starts, how many lines, and the message
            review_comment = Review.Comment(file_metadata['id'],
                                            first_line=1, num_lines=1,
                                            message=random_mean_girl_quote)
            # Broken Feature
            review_comment.severity = 'major'

            review_comment.raise_issue = True
            review.comments.append(review_comment)

        # Send that baby off!
        review.send(self.bio())

        ########################
        # Meangirl doesn't actually care about her comments so she doesn't need the things below, but you might
        #######################

        # If you find your self needing to convert real file names to botfood file names
        #file_name = real_file_name i.e /path/to/file
        #file_path = self.convert_real_filename_to_botfood_file_path(self.get_latest_revision_num(), file_name)

        # If you need a way to convert a patched file line to a unified diff line
        #line_map = self.get_patched_file_line_to_unified_diff_line_map(file_path)



# Boiler Plate, you must include this your bot.
def main(inputdir, config):
    MeanGirl(inputdir, config).run()


# Boiler Plate, you must include this in your bot.
# Though it you wanted you could create your own 'do_you_care' function
# The 'do_you_care' function is used by the BotManager in order to determine if a changelist
# warrants activating the bot for a review request. Look inside of bot.py to see what the default behaviour is.
def do_you_care(changes, botname):
    return Bot.do_you_care(changes, botname)

