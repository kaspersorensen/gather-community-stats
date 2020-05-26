import sys, getopt
from dataclasses import dataclass
import requests
from requests.auth import HTTPBasicAuth
from requests import Response

@dataclass(init=False)
class Arguments:
    subdomain: str = ""
    username: str = ""
    password: str = ""

def request_get(args: Arguments, path: str) -> Response:
    return requests.get(args.subdomain + path, auth=HTTPBasicAuth(args.username, args.password))

def get_topics(args: Arguments):
    resp = request_get(args, '/api/v2/community/topics.json')
    print(resp.text)
    return []

def run_main(args: Arguments):
    topics = get_topics(args)
    for topic in topics:
        print("--- TOPIC: " + topic.name + " ---")

def main(argv):
    HELP_LINE = 'main.py -d <subdomain> -u <username> -p <password>'
    arguments = Arguments()
    opts = []
    try:
        opts, args = getopt.getopt(argv,"hd:u:p:",["subdomain=", "username=","password="])
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
    run_main(arguments)

if __name__ == "__main__":
   main(sys.argv[1:])

