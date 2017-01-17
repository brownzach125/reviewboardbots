# reviewboardbots

Robots that review requests on [reviewboard servers](www.reviewboard.org)

## How it works

###### Request Polling
A watcher object regularly polls the targeted review board server for review requests.
The watcher filters out requests that aren't for any of the configured review bots and any
requests that haven't changed since the last time the request was polled.

The watcher creates a _botfood directory object_ for each request that gets throught the filtering proccess.
_botfood directory objects_ are a directory that contains the request information.

###### Queueing Jobs
Then the watcher passes those requests and their changelists to the botmanager.
 The botmanager works with the changelists and the bots themselves determines which bots care about the requests. For every bot that cares about the request and it's changelist
a job will be queued.

###### Completing Jobs
Workers then consume the jobs by running the bot's configured script on the _botfood directory object_
of the request. After that it's all up to the bot script

###### Posting a review
Most bot scripts will eventually post a review.

## Setup

1. Clone the repo
2. Run the python install script
3. Edit the config.json
4. Run python main.py

   There are known issues with the file structure. You'll probbally need to change some paths.

## Making your own bots.

Look at meangirl for inspiration. That bot is basically the bare minimum.
Beyond that look into the Bot parent class to get an idea of what methods are available.


