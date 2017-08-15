#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import

import os
import sys
import time
import json
import urllib

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
        if self.bot.login_status is not True:
            print('Login failed')
            self.die()

    def die(self):
        self.bot.cleanup()

    def get_user_profile(self, user_name):
        time.sleep(1)
        print("GET USER PROFILE ", user_name)
        response = self.bot.s.get(
            SureBot.ENDPOINTS['user_profile'].format(user_name))
        if response.status_code is not 200:
            print("User '{0}' not found: {1}".format(
                user_name, response.status_code))
            return None

        return json.loads(response.text)

    def get_user_followers(self, user_name, max_followers=20):
        time.sleep(1)
        print("GET USER FOLLOWERS ", user_name)
        user = self.get_user_profile(user_name)
        if not user or user['user']['is_private'] or user['user']['has_blocked_viewer']:
            print("User '{0}' not found, or is a private account, or they've blocked you!".format(user_name))
            return
        current_user_followers = []
        end_cursor = None
        has_next = False

        def fetch():
            time.sleep(1)
            params = {'id': user['user']['id'], 'first': 20}
            if end_cursor: params['after'] = end_cursor

            response = self.bot.s.get(self._build_query(params))
            if response.status_code is not 200:
                print("Followers for '{0}' could not be fetched: {1}".format(user_name, response.status_code))
                return

            data = json.loads(response.text)


        def work():
            while len(current_user_followers) < max_followers and has_next:
                fetch()
            return current_user_followers

        work()

    # Privates ----------
    def _build_query(self, params, query=FOLLOWERS):
        data = urllib.urlencode({"variables": json.dumps(params)})
        url = data.encode('utf-8')
        return '{3}{0}?query_id={1}&{2}'.format(SureBot.ENDPOINTS['graphql'],
                                                SureBot.QUERY_IDS[query], url,
                                                SureBot.ENDPOINTS['insta_home'])
