from rbtools.api.client import RBClient
import logging


class ResponseAgent:
    """When you just have to say something"""

    def __init__(self, server, name, password):
        self.client = RBClient(server, username=name, password=password)
        self.name = name

    def respond(self, response):

        root = self.client.get_root()

        logging.info(self.name + " is responding to review request " + str(response['request_id']))
        request = root.get_review_request(review_request_id=response['request_id'])
        review = request.get_reviews().create(body_top="")
        diff_comments = review.get_diff_comments

        for comment in response['diff_comments']:
            diff_comments().create(**comment)

        response.pop('diff_comments', None)
        response.pop('request_id', None)

        #review.update(body_top=response['body_top'], ship_it=response['ship_it'], )
        response['body_top'] = ResponseAgent.review_header() + "\n\n\n" + response['body_top']
        review.update(**response)

    @staticmethod
    def review_header():
        """For usability reasons, all reivews posted by reviewboard bots should have some general information."""
        return "You are being reviewed by a review board bot! If you have any questions or notice any issues contact " \
               "Zach Brown at zach.brown@ni.com. Or visit this repo and leave an issue. \n https://github.com/brownzach125/reviewboardbots Also feel free to contribute!" \

