import os
import logging
import requests
from datetime import datetime
from flask import current_app
from models import (
    db,
    GitHubToken,
    RepositorySubscription,
    UserRepository,
    TokenRepository,
    SubscriptionRepository,
    TestRunRepository
)

logger = logging.getLogger(__name__)

GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REDIRECT_URI')

class GitHubService:
    @staticmethod
    def get_user_info(access_token):
        resp = requests.get(
            "https://api.github.com/user",
            headers={'Authorization': f'token {access_token}', 'Accept': 'application/vnd.github.v3+json'}
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_user_repositories(access_token):
        resp = requests.get(
            "https://api.github.com/user/repos",
            headers={'Authorization': f'token {access_token}', 'Accept': 'application/vnd.github.v3+json'},
            params={'sort': 'updated', 'per_page': 100}
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def get_repository_events(access_token, repository_url):
        owner_repo = repository_url.rstrip('/').split('github.com/')[-1]
        events_url = f"https://api.github.com/repos/{owner_repo}/events"
        resp = requests.get(
            events_url,
            headers={'Authorization': f'token {access_token}', 'Accept': 'application/vnd.github.v3+json'}
        )
        if resp.status_code != 200:
            logger.warning(f"Events fetch failed for {owner_repo}: {resp.status_code}")
            return None
        return resp.json()

    @staticmethod
    def exchange_code_for_token(code):
        resp = requests.post(
            "https://github.com/login/oauth/access_token",
            data={'client_id': GITHUB_CLIENT_ID, 'client_secret': GITHUB_CLIENT_SECRET, 'code': code, 'redirect_uri': REDIRECT_URI},
            headers={'Accept': 'application/json'}
        )
        resp.raise_for_status()
        return resp.json().get('access_token')

class AuthService:
    @staticmethod
    def authenticate_user(github_code):
        token = GitHubService.exchange_code_for_token(github_code)
        info = GitHubService.get_user_info(token)
        username = info.get('login')
        print(username)
        user = UserRepository.get_by_username(username) or UserRepository.create(username)
        TokenRepository.store(user.id, token)
        print(user)
        return user

class SubscriptionService:
    @staticmethod
    def create_subscription(user_id, repository_full_name):
        url = f"https://github.com/{repository_full_name}"
        return SubscriptionRepository.create(user_id, url)

    @staticmethod
    def process_repository_events(subscription, events):
        new_pushes = []
        if subscription.last_event_id:
            for event in events:
                if event['id'] == subscription.last_event_id:
                    break
                if event['type'] == 'PushEvent':
                    new_pushes.append(event)
        else:
            for event in events:
                if event['type'] == 'PushEvent':
                    SubscriptionRepository.update_last_event(subscription, event['id'])
                    return []

        if new_pushes:
            SubscriptionRepository.update_last_event(subscription, new_pushes[0]['id'])
        return list(reversed(new_pushes))

class TestRunService:
    @staticmethod
    def enqueue_regeneration_task(user_id, repository_url):
        logger.info(f"Enqueue regeneration for {repository_url} (user {user_id})")
        subs = SubscriptionRepository.get_user_subscriptions(user_id)
        sub = next((s for s in subs if s.repository_url == repository_url), None)
        if not sub:
            logger.warning(f"No subscription for {repository_url}")
            return None
        return TestRunRepository.create(sub.id, status="pending", new_tests=0, removed_tests=0)



