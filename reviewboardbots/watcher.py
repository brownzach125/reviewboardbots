import time
from rbtools.api.client import RBClient
import datetime
from tinydb import TinyDB, Query
from bots.botfood import BotFood


def parse_server_time_stamp(timestamp):
    return datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%SZ")


class Watcher:
    """The thing that watches review board for things"""
    def __init__(self, server, bot_manager, bot_name_list, creds):
        print("The watcher is born")
        self.creds = creds
        self.server = server
        self.client = RBClient(server, username=creds['username'], password=creds['password'])

        self.bot_name_list = bot_name_list

        self.bot_manager = bot_manager
        self.time_obj = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
        self.newest_request_seen_timestamp = self.time_obj.isoformat()
        self.requests_seen = {}
        self.keep_watching = False
        self.bot_food_path = "/home/zbrown/reviewboardbots/reviewboardbots/botfood"
        self.data = Data(self.client, self.bot_food_path, self.bot_name_list)

    def set_newest_timestamp(self, requests):
        """We want to filter requests out from the server, but need to use its timestamps"""
        time_max = self.time_obj
        for request in requests:
            "Get timestamp from newest request in this group and inc by microsecond :)"
            time_str = request.last_updated
            time_obj = parse_server_time_stamp(time_str)

            if time_obj.time() > time_max.time():
                time_max = time_obj

        if time_max != self.time_obj:
            self.time_obj = time_max
            self.time_obj += datetime.timedelta(seconds=1)
            print "Updating time " + self.time_obj.isoformat()
            self.newest_request_seen_timestamp = self.time_obj.isoformat()

    def get_new_requests(self):
        """get reviews after the timestamp"""
        root = self.client.get_root()
        # requests = root.get_review_requests(last_updated_from=self.newest_request_seen_timestamp)
        requests = root.get_review_requests()

        requests = self.filter_out_requests_not_for_our_bots(requests)

        # Set the timestamp for next time
        self.set_newest_timestamp(requests)

        return requests

    def filter_out_requests_not_for_our_bots(self, requests):
        filtered_requests = []
        for request in requests:
            for person in request.target_people:
                if person.title in self.bot_name_list:
                    filtered_requests.append(request)
                    break
        return filtered_requests

    def watch(self):
        """Periodically check for new reviews, spin off bots when needed"""
        self.keep_watching = True

        "Until my watch is ended"
        print("Watcher: I am watching")
        while self.keep_watching:
            try:
                new_requests = self.get_new_requests()
                self.data.add_requests(new_requests)

                requests_in_need_of_attention = self.data.fresh_requests()
                self.bot_manager.process_new_requests(requests_in_need_of_attention)
                self.data.mark_attended(requests_in_need_of_attention)
            except:
                # If something goes wrong, create a new client and move on.
                # It's a little too broad, but it should keep the lights on.
                self.client = RBClient(self.server, username=self.creds['username'], password=self.creds['password'])
            time.sleep(60)


        print("Watcher: My watch has ended")

    def stop(self):
        self.keep_watching = False


class Data:
    def __init__(self, client, botfood_path, bot_name_list):
        self.db = TinyDB('db.json')
        self.request_table = self.db.table('requests')
        self.rb_client = client
        self.bot_name_list = bot_name_list
        self.botfood_path = botfood_path

    def fresh_requests(self):
        Request = Query()
        return self.request_table.search(Request.needs_attention != False)

    def mark_attended(self, requests):
        Request = Query()
        for request in requests:
            self.request_table.update({'needs_attention': False, 'new_changes': []}, Request.id == request["id"])

    def add_requests(self, requests):
        for raw_request in requests:
            Request = Query()
            request = {
                "id": raw_request["id"],
                "bots": [bot.title for bot in raw_request.target_people if bot.title in self.bot_name_list],
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
                request['bot_food_path'] = BotFood(raw_request).save(self.botfood_path)
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
