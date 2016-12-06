from rbtools.api.client import RBClient


class ResponseAgent:
    """When you just have to say something"""

    def __init__(self, server, name, password):
        self.client = RBClient(server, username=name, password=password)
        print("Response agent created")

    def respond(self, response):

        root = self.client.get_root()

        request = root.get_review_request(review_request_id=response['request_id'])
        review = request.get_reviews().create(body_top="")
        diff_comments = review.get_diff_comments
        "This link does not exist :((((("
        #general_comments = review.get_general_comments()
        for comment in response['diff_comments']:
            diff_comments().create(**comment)
        "TODO general comments are broken I don\'t know what\'s up with that :("
        for comment in response['general_comments']:
            diff_comments().create(**comment)

        review.update(**response)
