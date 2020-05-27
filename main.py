import sys, getopt, datetime
from datetime import datetime, timedelta
import pytz
from dataclasses import dataclass
import requests
from requests.auth import HTTPBasicAuth
from requests import Response

utc = pytz.UTC

@dataclass(init=False)
class Arguments:
    subdomain: str = None
    username: str = None
    token: str = None
    outputfile: str = None
    filter_from: datetime = None
    filter_to: datetime = None

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

def included_in_date_range(args: Arguments, datestr):
    if not args.filter_from and not args.filter_to:
        return True
    dt = datetime.strptime(datestr, "%Y-%m-%dT%H:%M:%S%z")
    if args.filter_from and args.filter_from > dt:
        return False
    if args.filter_to and args.filter_to < dt:
        return False
    return True

def older_than_date_range(args: Arguments, datestr):
    if not args.filter_from:
        return False
    dt = datetime.strptime(datestr, "%Y-%m-%dT%H:%M:%S%z")
    if args.filter_from and args.filter_from > dt:
        return True
    return False

def get_posts(args: Arguments, topic_id = None):
    if topic_id:
        resp = request_get(args, f'/api/v2/community/topics/{topic_id}/posts.json?sort_by=recent_activity')
    else:
        resp = request_get(args, f'/api/v2/community/posts.json?sort_by=recent_activity')
    keep_running = True
    while keep_running:
        body = resp.json()
        for post in body['posts']:
            if included_in_date_range(args, post['created_at']):
                yield post
            elif included_in_date_range(args, post['updated_at']):
                # still relevant to yield this because comments has to be observed
                yield post
            elif older_than_date_range(args, post['created_at']):
                # no reason to read any further
                keep_running = False
        if keep_running:
            if body['next_page']:
                resp = request_get(args, body['next_page'])
            else:
                keep_running = False

def get_comments(args: Arguments, post_id):
    resp = request_get(args, f'/api/v2/community/posts/{post_id}/comments.json')
    keep_running = True
    while keep_running:
        body = resp.json()
        for comment in body['comments']:
            if included_in_date_range(args, comment['created_at']):
                yield comment
            elif older_than_date_range(args, comment['created_at']):
                # no reason to read any further
                keep_running = False
        if keep_running:
            if body['next_page']:
                resp = request_get(args, body['next_page'])
            else:
                keep_running = False

def run_main(args: Arguments):
    stats = UserStats()
    topic_id = None
    posts = get_posts(args, topic_id)
    for post in posts:
        if included_in_date_range(args, post['created_at']):
            stats.observe_post_by_user(post['author_id'])
        comments = get_comments(args, post['id'])
        for comment in comments:
            stats.observe_comment_by_user(comment['author_id'])
    if args.outputfile:
        with open(args.outputfile, "w") as f:
            for line in stats.to_csv():
                f.write(line)
                f.write('\n')
        print(f"Results saved to {args.outputfile}")
    else:
        print("--- RESULTS ---")
        for line in stats.to_csv():
            print(line)

def main(argv):
    HELP_LINE = 'main.py -d <subdomain> -u <username> -t <token> --from=<from> --to=<to>'
    arguments = Arguments()
    opts = []
    try:
        opts, args = getopt.getopt(argv,"ho:d:u:t:",["output=","subdomain=","username=","token=","from=","to="])
    except getopt.GetoptError as e:
        print(e)
        print(HELP_LINE)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help", "--usage", "-?"):
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
        elif opt in ("-o", "--output"):
            arguments.outputfile = arg
        elif opt in ("--from"):
            dt = datetime.strptime(arg, "%Y-%m-%d")
            arguments.filter_from = utc.localize(dt=dt)
        elif opt in ("--to"):
            dt = datetime.strptime(arg, "%Y-%m-%d")
            dt = dt + timedelta(days=1, seconds=-1) # add one day minus one second to make "to" inclusive
            arguments.filter_to = utc.localize(dt=dt)
    run_main(arguments)

if __name__ == "__main__":
   main(sys.argv[1:])
