import os
from botfood import BotFood
import subprocess
class BotManager:
    """Handles the bots"""
    def __init__(self, bot_food_dir, bot_dir):
        if not os.path.exists(bot_food_dir):
            os.mkdir(bot_food_dir)
        self.bot_food_dir = bot_food_dir
        self.bot_dir = bot_dir

    def processNewReviews(self, reviews):
        """reviews key;botname, value: listofreviews"""
        for botname in reviews:
                botfood = BotFood(reviews[botname])
                reviewPath = botfood.save(os.path.join(self.bot_food_dir, botname))

                "Dumbly start a bot instance "
                for review in reviews[botname]:
                    print("Bot manager would like to start " + botname)
                    
                    path = os.path.join(os.path.join(self.bot_dir, botname), "start.py")
                    if os.path.isfile(path):
                        #TODO: escape to handle whitespace in filenames
                        print subprocess.Popen(["python", path, reviewPath], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
                    else:
                        print "path not found"

