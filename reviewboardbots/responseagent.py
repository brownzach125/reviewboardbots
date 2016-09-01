from rbtools.api.client import RBClient


class ResponseAgent:
    """When you just have to say something"""

    def __init__(self, server, name, password):
        self.client = RBClient(server, \
                               username=name,
                               password=password)
        print("Response agent created")

    def respond(self, response):

        root = self.client.get_root()

        request = root.get_review_request(review_request_id=response['request_id'])
        review = request.get_reviews().create()
        diff_comments = review.get_diff_comments
        general_comments = review.get_replies()
        for comment in response['diff_comments']:
            diff_comments().create(**comment)
        for comment in response['general_comments']:
            general_comments().create(**comment)
        review.update(body_top=response['message'], public=True, ship_it=response['ship_it'])

