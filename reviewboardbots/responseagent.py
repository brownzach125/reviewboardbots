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

        for comment in response['diff_comments']:
            diff_comments().create(**comment)

        response.pop('diff_comments', None)
        response.pop('request_id', None)

        #review.update(body_top=response['body_top'], ship_it=response['ship_it'], )
        review.update(**response)
