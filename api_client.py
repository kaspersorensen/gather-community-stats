import requests
from requests.auth import HTTPBasicAuth
from requests import Response
import api_util

class ApiClient:
    def __init__(self, subdomain, username, token):
        self.subdomain = subdomain
        self.username = username
        self.token = token
    def get_user(self, user_id):
        resp = self.__http_get(f'/api/v2/users/{user_id}.json')
        return resp.json()['user']
    def get_topics(self):
        resp = self.__http_get('/api/v2/community/topics.json')
        return resp.json()['topics']
    def get_badges(self):
        resp = self.__http_get('/api/v2/gather/badges')
        return resp.json()['badges']
    def create_badge_assignment(self, user_id, badge_id):
        resp = self.__http_post('/api/v2/gather/badge_assignments', {
            "badge_assignment": {
                "badge_id": badge_id,
                "user_id": user_id
            }
        })
        return resp.json()
    def get_posts(self, topic_id = None, filter_from: str = None, filter_to: str = None):
        if topic_id:
            resp = self.__http_get(f'/api/v2/community/topics/{topic_id}/posts.json?sort_by=recent_activity')
        else:
            resp = self.__http_get(f'/api/v2/community/posts.json?sort_by=recent_activity')
        keep_running = True
        while keep_running:
            body = resp.json()
            for post in body['posts']:
                if api_util.included_in_date_range(post['created_at'], filter_from, filter_to):
                    yield post
                elif api_util.included_in_date_range(post['updated_at'], filter_from, filter_to):
                    # still relevant to yield this because comments has to be observed
                    yield post
                elif api_util.older_than_date_range(post['created_at'], filter_from):
                    # no reason to read any further
                    keep_running = False
            if keep_running:
                if body['next_page']:
                    resp = self.__http_get(body['next_page'])
                else:
                    keep_running = False

    def get_comments(self, post_id, filter_from: str = None, filter_to: str = None):
        resp = self.__http_get(f'/api/v2/community/posts/{post_id}/comments.json')
        keep_running = True
        while keep_running:
            body = resp.json()
            for comment in body['comments']:
                if api_util.included_in_date_range(comment['created_at'], filter_from, filter_to):
                    yield comment
                elif api_util.older_than_date_range(comment['created_at'], filter_from):
                    # no reason to read any further
                    keep_running = False
            if keep_running:
                if body['next_page']:
                    resp = self.__http_get(body['next_page'])
                else:
                    keep_running = False
    def __http_get(self, path: str) -> Response:
        if path.startswith('http'):
            url = path
        else:
            url = self.subdomain + path
        print(f'GET {url}')
        return requests.get(url, auth=HTTPBasicAuth(self.username + "/token", self.token))
    def __http_post(self, path: str, json_body: dict) -> Response:
        if path.startswith('http'):
            url = path
        else:
            url = self.subdomain + path
        return requests.post(url, json=json_body, auth=HTTPBasicAuth(self.username + "/token", self.token))
