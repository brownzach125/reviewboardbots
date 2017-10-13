from tinydb import TinyDB, Query
from botfood import BotFood


# A watcher's memory
# The magic database object, which does a lot of the filtering work
# lets the watcher keep track of which reviews it's seen before and if they've changed enough
# to warrant action
class WatcherMemory:
    def __init__(self, client, botfood_path, bot_list):
        self.db = TinyDB('db.json')
        self.request_table = self.db.table('requests')
        self.rb_client = client
        self.bot_name_list = bot_list.keys()
        self.bot_list = bot_list
        self.botfood_path = botfood_path

    def fresh_requests(self):
        Request = Query()
        return self.request_table.search(Request.needs_attention != False)

    def mark_attended(self, requests):
        Request = Query()
        for request in requests:
            self.request_table.update({'needs_attention': False, 'new_changes': []}, Request.id == request["id"])

    def add_requests(self, requests, rb_client):
        for raw_request in requests:
            Request = Query()

            reviewers = [bot.title for bot in raw_request.target_people if bot.title in self.bot_name_list]
            groups = [our_bot
                      for our_bot in self.bot_name_list
                      if any(group.title
                             in self.bot_list[our_bot]
                             for group in raw_request.target_groups)]

            request = {
                "id": raw_request["id"],
                "bots": [bot for bot in set().union(reviewers, groups)],
            }

            entry = self.request_table.search(Request.id == raw_request["id"])
            if not entry:
                self.request_table.insert(request)
            else:
                request['old_bots'] = entry[0]['bots']
                self.request_table.update(request, Request.id == raw_request["id"])

            # LOL Lazy, but who cares? it works
            request = self.request_table.search(Request.id == raw_request["id"])[0]
            request['needs_attention'], request['new_changes'] = self.request_need_attention(raw_request, request)
            # Only save the bot food if we think anyone will care
            if request['needs_attention']:
                request['bot_food_path'] = BotFood(raw_request, rb_client=rb_client).save(self.botfood_path)
            self.request_table.update(request, Request.id == raw_request["id"])

    # Does a request need attention and if so from who?
    def request_need_attention(self, raw_request, request):
        change_list = self.rb_client.get_root().get_changes(review_request_id=raw_request.id)
        change_list = [BotFood.flatten_resource(r) for r in change_list]

        # Oh well if we haven't even placed the key change_list into request it must be new
        if "change_list" not in request:
            request['change_list'] = change_list
            return True, change_list

        if not len(change_list):
            # Okay so since the condition above didn't happen and the list is empty then
            return False, []

        if not len(request['change_list']):
            # Okay there is a request['change_list'] option, but it's empty and change_list is not
            # send change list!
            request['change_list'] = change_list
            return True, change_list

        # Obviously if the change list has not changed in size then there are no changes
        # Holy shit it turns out they only store 25 changes tops!!!!! fuck
        # Okay well they id the changes, so if the top of the two lists is the same, well there you have it
        if request['change_list'][0]['id'] == change_list[0]['id']:
            return False, []

        # Okay so there are some new changes, get those
        new_changes = change_list[:len(request['change_list'])]

        # Save the new change list to the request now that we're done with the old one
        request['change_list'] = change_list

        return True, new_changes
