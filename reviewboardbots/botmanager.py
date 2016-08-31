import os
from botfood import BotFood
from subprocess import Popen

class BotManager:
    """Handles the bots"""
    def __init__(self, bot_dict):
        self.bots = bot_dict

    def processNewReviews(self, requests):
        """reviews key;botname, value: listofreviews"""
        for botname in requests:
                bot = self.bots[botname]

                "Make bot food out of this request"
                botfood = BotFood(requests[botname])
                botfood.save(bot['food_dir'])

                self.queueNewRequests(requests[botname], bot)

    def queueNewRequests(self, request_list, bot):
        """Dumbly start a bot instance """
        for request in request_list:
            request_id = request.id
            print("Bot manager would like to start " + bot['name'] + " for " + str(request_id))
            print "Request Time " + request.last_updated

            script_path = bot['script']
            food_path = os.path.join(bot['food_dir'], 'request' + str(request_id))

            Popen(['python', script_path, "-i", food_path])

