from rbtools.api.client import RBClient
import logging


def review_header():
    """For usability reasons, all reivews posted by reviewboard bots should have some general information."""
    from config import config
    if 'header' in config:
        return config['header']
    else:
        return "You are being reviewed by a review board bot! If you have any questions or notice any issues contact " \
               "Zach Brown at zach.brown@ni.com. Or visit this repo and leave an issue. \n" \
               " https://github.com/brownzach125/reviewboardbots Also feel free to contribute!"


###########################
# Representation of reviewboard review
# bots create review objects and then send them
###########################
class Review:
    class Comment:
        def __init__(self, file_id, first_line, num_lines, message):
            self.file_id = file_id
            self.first_line = first_line
            self.num_lines = num_lines
            self.message = message

            self.raise_issue = False

            self.severity = 'info'

    def __init__(self, server, name, password, request_id, rev_id):
        self.server = server
        self.name = name
        self.password = password
        self.request_id = request_id
        self.rev_id = rev_id

        self.header = ""
        self.ship_it = True

        self.comments = []

    def send(self, bot_bio):
        print self.name + 'I sent myself'
        client = RBClient(self.server, username=self.name, password=self.password)
        root = client.get_root()

        logging.info(self.name + " is responding to review request " + str(self.request_id))
        request = root.get_review_request(review_request_id=self.request_id)
        review = request.get_reviews().create(body_top="")
        diff_comments = review.get_diff_comments

        for comment in self.comments:
            diff_comments().create(**{
                'filediff_id': comment.file_id,
                'first_line': comment.first_line,
                'num_lines': comment.num_lines,
                'text': comment.message,
                'issue_opened': comment.raise_issue,
                'extra_data': {
                    'severity': comment.severity
                }
            })

        # review.update(body_top=response['body_top'], ship_it=response['ship_it'], )
        if not bot_bio:
            bot_bio = ""
        review.update(**{
            'body_top': "{0}\n\n\n{1}\n\n\n{2}".format(review_header(), bot_bio, self.header),
            'ship_it': self.ship_it,
            'public': True,
            'request_id': self.request_id
        })


class ResponseAgent:
    """When you just have to say something"""

    def __init__(self, server, name, password):
        self.client = RBClient(server, username=name, password=password)
        self.name = name

    ###
    # How to actually send a response
    ###
    def respond(self, response, bio):
        root = self.client.get_root()

        logging.info(self.name + " is responding to review request " + str(response['request_id']))
        request = root.get_review_request(review_request_id=response['request_id'])
        review = request.get_reviews().create(body_top="")
        diff_comments = review.get_diff_comments

        for comment in response['diff_comments']:
            diff_comments().create(**comment)

        response.pop('diff_comments', None)
        response.pop('request_id', None)

        # review.update(body_top=response['body_top'], ship_it=response['ship_it'], )
        if not bio:
            bio = ""
        response['body_top'] = "{0}\n\n\n{1}\n\n\n{2}".format(review_header(), bio, response['body_top'])
        review.update(**response)

    def create_review(self, request_id, revision_id=1, message="Default bot review message", ship_it=False):
        """Creates the bareminimum review, feel free to add more once you have it"""
        return {
            'body_top': message,
            'ship_it': ship_it,
            'diff_comments': [],
            'public': True,
            'request_id': request_id
        }

    def create_diff_comment(self, filediff_id, first_line, num_lines, text):
        """Creates the bare minium diff comment, feel free to add more once you have it"""
        return {
            'filediff_id': filediff_id,
            'first_line': first_line,
            'num_lines': num_lines,
            'text': text
        }

    # @staticmethod
    # def review_header():
    #     """For usability reasons, all reivews posted by reviewboard bots should have some general information."""
    #     return review_header()
