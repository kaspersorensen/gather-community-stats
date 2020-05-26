import sys, getopt
from dataclasses import dataclass
import requests
from requests.auth import HTTPBasicAuth
from requests import Response

@dataclass(init=False)
class Arguments:
    subdomain: str = ""
    username: str = ""
    token: str = ""

class UserStats:
    def __init__(self):
        self.stats_by_user = dict()
    def observe_post_by_user(self, user_id):
        userstats = self.stats_by_user.get(user_id)
        if not userstats:
            userstats = dict()
            self.stats_by_user[user_id] = userstats
        userstats['posts'] = 1 + (userstats.get('posts') or 0)
    def observe_comment_by_user(self, user_id):
        userstats = self.stats_by_user.get(user_id)
        if not userstats:
            userstats = dict()
            self.stats_by_user[user_id] = userstats
        userstats['comments'] = 1 + (userstats.get('comments') or 0)
    def to_csv(self):
        yield 'user_id,num_posts,num_comments'
        for user_id in self.stats_by_user:
            userstats = self.stats_by_user[user_id]
            num_posts = userstats.get('posts') or 0
            num_comments = userstats.get('comments') or 0
            yield f"{user_id},{num_posts},{num_comments}"

def request_get(args: Arguments, path: str) -> Response:
    if path.startswith('http'):
        url = path
    else:
        url = args.subdomain + path
    print(f'GET {url}')
    return requests.get(url, auth=HTTPBasicAuth(args.username + "/token", args.token))

def get_topics(args: Arguments):
    resp = request_get(args, '/api/v2/community/topics.json')
    return resp.json()['topics']

def get_posts(args: Arguments, topic_id = None):
    if topic_id:
        resp = request_get(args, f'/api/v2/community/topics/{topic_id}/posts.json')
    else:
        resp = request_get(args, f'/api/v2/community/posts.json')
    keep_running = True
    while keep_running:
        body = resp.json()
        for post in body['posts']:
            yield post
        if body['next_page']:
            resp = request_get(args, body['next_page'])
        else:
            keep_running = False

def get_comments(args: Arguments, post_id):
    resp = request_get(args, f'/api/v2/community/posts/{post_id}/comments.json')
    return resp.json()['comments']

def run_main(args: Arguments):
    stats = UserStats()
    topic_id = None
    posts = get_posts(args, topic_id)
    for post in posts:
        stats.observe_post_by_user(post['author_id'])
        comments = get_comments(args, post['id'])
        for comment in comments:
            stats.observe_comment_by_user(comment['author_id'])
    print("--- RESULTS ---")
    for line in stats.to_csv():
        print(line)

def main(argv):
    HELP_LINE = 'main.py -d <subdomain> -u <username> -t <token>'
    arguments = Arguments()
    opts = []
    try:
        opts, args = getopt.getopt(argv,"hd:u:t:",["subdomain=","username=","token="])
    except getopt.GetoptError:
        print(HELP_LINE)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print(HELP_LINE)
            sys.exit()
        elif opt in ("-d", "--subdomain"):
            subdomain = arg
            if not '.' in subdomain:
                subdomain = subdomain + '.zendesk.com'
            if not subdomain.startswith('http'):
                subdomain = 'https://' + subdomain
            arguments.subdomain = subdomain
        elif opt in ("-u", "--username"):
            arguments.username = arg
        elif opt in ("-p", "--password"):
            arguments.password = arg
        elif opt in ("-t", "--token"):
            arguments.token = arg
    run_main(arguments)

if __name__ == "__main__":
   main(sys.argv[1:])

