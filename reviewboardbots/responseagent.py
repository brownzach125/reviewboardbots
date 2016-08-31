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
        for comment in response['comments']:
            review.get_diff_comments().create(
                filediff_id=comment['filediff_id'],
                first_line=comment['first_line'],
                num_lines=comment['num_lines'],
                text=comment['text']
            )
        review.update(body_top=response['message'], public=True, ship_it=response['ship_it'])

#agent = ResponseAgent("http://pds-rbdev01" ,"meangirl", "meangirl")
#response = {
#    'request_id': 45,
#    'revision_id': 1,
#    'comments': [
#        {
#            'filediff_id':114,
#            'first_line':1,
#            'num_lines':1,
#            'text':'I loooooovvvvve your bracelet'
#        }
#    ],
#    'message': "You\'re like obsessed with me",
#    'ship_it' : True
#}
#agent.respond(response)
