import threading
import time

from bots.botfood import BotFood
from threading import RLock, Condition, Lock
import importlib


class BotManager:
    """Handles the bots"""
    def __init__(self, bot_dict, max_threads=5):
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

            bot = job['bot']
            bot['active'] += 1
            self.queueLock.release()

            # Do the job
            try:
                bot['code'].main(["-i", job['path']])
            except Exception as e:
                print e
            finally:
                self.queueLock.acquire()
                bot['active'] -= 1
                self.queueLock.notify()
                self.queueLock.release()

    # Use by the watcher to hand over new requests
    def process_new_requests(self, requests):
        """requests key;botname, value: listofrequests"""
        for bot_name in requests:
                bot = self.bots[bot_name]

                "Make bot food out of these requests and pass it on"
                try:
                    bot_food = BotFood(requests[bot_name])
                    paths = bot_food.save(bot['food_dir'])
                    self.queue_requests(paths, bot)
                except Exception as e:
                    print e

    def queue_requests(self, paths, bot):
        self.queueLock.acquire()
        for path in paths:
            self.queue.append({
                "path": path,
                "bot": bot
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

foreman = BotManager({
    "bobby" : {
        "name" : "bobby",
        "script" : "bots.linux_kernel_checkpatch",
    }
})

# They must be absolute paths!!!!!!!!!!! Look into making bot_food do this
foreman.queue_requests(["../checkpatchfood/request178"], foreman.bots["bobby"])
foreman.start()
foreman.queue_requests(["./checkpatchfood/request178"], foreman.bots["bobby"])
time.sleep(3)
foreman.stop()

print "All done now"


