import sys, getopt, datetime
from datetime import datetime, timedelta
import pytz
from dataclasses import dataclass
from api_client import ApiClient
import api_util

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

def run_main(args: Arguments):
    api = ApiClient(args.subdomain, args.username, args.token)
    stats = UserStats()
    topic_id = None
    posts = api.get_posts(topic_id, filter_from=args.filter_from, filter_to=args.filter_to)
    for post in posts:
        if api_util.included_in_date_range(post['created_at'], filter_from=args.filter_from, filter_to=args.filter_to):
            stats.observe_post_by_user(post['author_id'])
        comments = api.get_comments(post['id'], filter_from=args.filter_from, filter_to=args.filter_to)
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
