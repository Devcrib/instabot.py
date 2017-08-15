#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import

import os
import sys
import time
import json
import urllib
import random

sys.path.append(os.path.join(sys.path[0], 'src'))
from instabot import InstaBot


class SureBot:

    # consts
    FOLLOWERS = 'followers'
    FOLLOWING = 'following'
    QUERY_IDS = {
        FOLLOWERS: '17851374694183129',
        FOLLOWING: '17874545323001329'
    }
    ENDPOINTS = {
        'insta_home': 'https://www.instagram.com',
        'user_profile': 'https://www.instagram.com/{0}/?__a=1',
        'graphql': '/graphql/query/'
    }

    def __init__(self, user_name='', password=''):
        # options
        self.user_name = user_name
        self.user_key = password
        self.my_profile = None

        # attempt login
        self.bot = InstaBot(login=self.user_name,
                            password=self.user_key, log_mod=0)
        if self.bot.login_status != True:
            print('Login failed')
            self.die()

    def die(self):
        self.bot.cleanup()

    def get_user_profile(self, user_name):
        self._sleep()
        print("GET USER PROFILE ", user_name)
        response = self.bot.s.get(
            SureBot.ENDPOINTS['user_profile'].format(user_name))
        if response.status_code != 200:
            print("User '{0}' not found: {1}".format(
                user_name, response.status_code))
            return None

        return json.loads(response.text)

    def get_user_followers(self, user_name, max_followers=20):
        self._sleep()
        print("GET USER FOLLOWERS ", user_name)
        user = self.get_user_profile(user_name)
        if not user or user['user']['is_private'] or user['user']['has_blocked_viewer']:
            print("User '{0}' not found, or is a private account, or they've blocked you!".format(
                user_name))
            return
        current_user_followers = []
        end_cursor = None
        has_next = True

        def fetch(current_user_followers, end_cursor, has_next):
            self._sleep()
            params = {'id': user['user']['id'], 'first': 3}
            if end_cursor:
                params['after'] = end_cursor
                # params['first'] = 10

            response = self.bot.s.get(self._build_query(params))
            if response.status_code != 200:
                print("Followers for '{0}' could not be fetched: {1}".format(
                    user_name, response.status_code))
                has_next = False
                return current_user_followers, end_cursor, has_next

            data = json.loads(response.text)
            if data['status'] != 'ok':
                print("Unable to fetch followers for '{0}'".format(user_name))
                has_next = False
                return current_user_followers, end_cursor, has_next

            data = data['data']
            if data['user']['edge_followed_by']['count'] == 0:
                print("User '{0}' has no followers".format(user_name))
                has_next = False
                return current_user_followers, end_cursor, has_next

            # go on with this user
            print("Fetched '{0}' of {1} follower(s)".format(len(
                data['user']['edge_followed_by']['edges']), data['user']['edge_followed_by']['count']))
            has_next = data['user']['edge_followed_by']['page_info']['has_next_page']
            end_cursor = data['user']['edge_followed_by']['page_info']['end_cursor']

            filtered = self._filter_followers(
                data['user']['edge_followed_by']['edges'])
            if filtered:
                current_user_followers += filtered
                
            return current_user_followers[:max_followers], end_cursor, has_next

        def work(current_user_followers, end_cursor, has_next):
            while len(current_user_followers) < max_followers and has_next:
                print('Calling fetch...', len(current_user_followers))
                current_user_followers, end_cursor, has_next = fetch(
                    current_user_followers, end_cursor, has_next)
                
            return current_user_followers

        current_user_followers = work(current_user_followers, end_cursor, has_next)
        return current_user_followers

    def interact(self, max_likes=5, comment_rate=.1):
        pass

    # Privates ----------
    def _filter_followers(self, followers):
        useful = []
        for follower in followers:
            user = self.get_user_profile(follower['node']['username'])
            if not user or user['user']['is_private'] or user['user']['has_blocked_viewer']:
                print("User '{0}' not found, or is a private account, or they've blocked you!".format(
                    follower['node']['username']))
                continue

            user = user['user']
            if user['follows_viewer'] or user['has_requested_viewer']:
                print("Skipping {0}, they follow you already".format(
                    user['username']))
                continue
            useful.append(
                {'username': user['username'], 'user_id': user['id']})
        random.shuffle(useful)
        return useful

    def _build_query(self, params, query=FOLLOWERS):
        data = urllib.urlencode({"variables": json.dumps(params)})
        url = data.encode('utf-8')
        return '{3}{0}?query_id={1}&{2}'.format(SureBot.ENDPOINTS['graphql'],
                                                SureBot.QUERY_IDS[query], url,
                                                SureBot.ENDPOINTS['insta_home'])

    def _sleep(self):
        s = random.choice(range(1, 4))
        time.sleep(s)
