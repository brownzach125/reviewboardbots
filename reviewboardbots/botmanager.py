import os
from botfood import BotFood
from subprocess import call

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
                botfood.save(os.path.join(self.bot_food_dir, botname))

                "Dumbly start a bot instance "
                for request in reviews[botname]:
                    request_id = request.id
                    print("Bot manager would like to start " + botname)
                    call([os.path.join(self.bot_dir, botname), "-i", \
                          os.path.join(self.bot_food_dir,  "request" + str(request_id))]) 

