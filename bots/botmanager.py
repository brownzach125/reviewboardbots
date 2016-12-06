import threading
import traceback

from threading import RLock, Condition
import importlib


class BotManager:
    """Handles the bots"""
    def __init__(self, bot_dict, server="", max_threads=5):
        self.bots = bot_dict
        self.being_paid = False
        self.threads = []
        self.max_threads = max_threads

        self.queueLock = Condition(RLock())
        self.queue = []

        # Some bot pre processing
        for bot_name, bot in self.bots.iteritems():
            bot['active'] = 0
            if 'max_concurrently' not in bot:
                bot['max_concurrently'] = 1
            bot['code'] = importlib.import_module(bot['script'])
            bot['server'] = server

    def start(self):
        self.being_paid = True
        for i in range(0, self.max_threads):
            self.threads.append(threading.Thread(target=self.run, args=[i]))
        for i in range(0, self.max_threads):
            self.threads[i].start()

    def stop(self):
        self.being_paid = False
        self.queueLock.acquire()
        self.queueLock.notifyAll()
        self.queueLock.release()
        for i in range(0, self.max_threads):
            self.threads[i].join()

    def run(self, id):
        while self.being_paid:
            # Get job
            self.queueLock.acquire()
            job = self.pop_request()
            while not job:
                self.queueLock.wait()
                if not self.being_paid:
                    return
                job = self.pop_request()

            print "I got a job"
            bot = job['bot']
            bot['active'] += 1
            self.queueLock.release()

            # Do the job
            try:
                bot['code'].main(job['path'], bot)
            except Exception as e:
                print e
                traceback.print_exc()
            finally:
                self.queueLock.acquire()
                bot['active'] -= 1
                self.queueLock.notify()
                self.queueLock.release()

    # Use by the watcher to hand over new requests
    def process_new_requests(self, requests):

        # Okay we're going to get a list of requests that have new changes
        # its up to the botmanager to figure out if the bots care, maybe he can ask them, eh that's for later
        for request in requests:
            for bot_name in request['bots']:
                bot = self.bots[bot_name]
                if len(request['new_changes']) == 0:
                    # new request all bots interested
                    self.queue_job(bot, request)
                    continue

                if bot['code'].do_you_care(request['new_changes'], bot['name']):
                    self.queue_job(bot, request)

    def queue_job(self, bot, request):
        self.queueLock.acquire()
        print "Queuing job"
        self.queue.append({
            "bot": bot,
            "path": request["bot_food_path"]
        })
        self.queueLock.notify()
        self.queueLock.release()

    def pop_request(self):
        # Find request with highest priority(been here the longest) and with free bot
        with self.queueLock:
            for index, job in enumerate(self.queue):
                bot_name = job["bot"]["name"]
                if self.bots[bot_name]["active"] < self.bots[bot_name]["max_concurrently"]:
                    self.queue.pop(index)
                    return job
