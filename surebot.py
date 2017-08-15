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
    MEDIA = 'media'
    QUERY_IDS = {
        FOLLOWERS: '17851374694183129',
        FOLLOWING: '17874545323001329',
        MEDIA: '17888483320059182'
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
        
        # stats
        self.likes = []

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

        while len(current_user_followers) < max_followers and has_next:
            self._sleep()
            params = {'id': user['user']['id'], 'first': 3}
            if end_cursor:
                params['after'] = end_cursor
                # params['first'] = 10

            response = self.bot.s.get(self._build_query(params))
            if response.status_code != 200:
                print("Followers for '{0}' could not be fetched: {1}".format(
                    user_name, response.status_code))
                return

            data = json.loads(response.text)
            if data['status'] != 'ok':
                print(
                    "Unable to fetch followers for '{0}'".format(user_name))
                return

            data = data['data']
            if data['user']['edge_followed_by']['count'] == 0:
                print("User '{0}' has no followers".format(user_name))
                return

            # go on with this user
            print("Fetched '{0}' of {1} follower(s)".format(len(
                data['user']['edge_followed_by']['edges']), data['user']['edge_followed_by']['count']))
            has_next = data['user']['edge_followed_by']['page_info']['has_next_page']
            end_cursor = data['user']['edge_followed_by']['page_info']['end_cursor']

            filtered = self._filter_followers(
                data['user']['edge_followed_by']['edges'])
            if filtered:
                current_user_followers += filtered

        return current_user_followers[:max_followers]

    def get_feed(self, user_name, max_media_count=20):
        user = self.get_user_profile(user_name)
        if not user or user['user']['is_private'] or user['user']['has_blocked_viewer']:
            print("User '{0}' not found, or is a private account, or they've blocked you!".format(
                user_name))
            return

        current_user_media = []
        end_cursor = None
        has_next = True

        while len(current_user_media) < max_media_count and has_next:
            self._sleep()
            params = {'id': user['user']['id'], 'first': 12}
            if end_cursor:
                params['after'] = end_cursor

            response = self.bot.s.get(self._build_query(params, SureBot.MEDIA))
            if response.status_code != 200:
                print("Media feed for '{0}' could not be fetched: {1}".format(
                    user_name, response.status_code))
                return

            data = json.loads(response.text)
            if data['status'] != 'ok':
                print(
                    "Unable to fetch media feed for '{0}'".format(user_name))
                return

            data = data['data']
            if data['user']['edge_owner_to_timeline_media']['count'] == 0:
                print("User '{0}' has no media uploaded".format(user_name))
                return

            # go on with this media feed
            print("Fetched '{0}' of {1} media".format(len(
                data['user']['edge_owner_to_timeline_media']['edges']),
                data['user']['edge_owner_to_timeline_media']['count']))
            has_next = data['user']['edge_owner_to_timeline_media']['page_info']['has_next_page']
            end_cursor = data['user']['edge_owner_to_timeline_media']['page_info']['end_cursor']

            # pick em media
            for media in data['user']['edge_owner_to_timeline_media']['edges']:
                media = media['node']
                current_user_media.append(
                    {'media_id': media['id'], 'media_type': 'video' if media['is_video'] else 'photo'})

        return current_user_media[:max_media_count]

    def feed_liker(self, feed):
        if not feed:
            print('Cannot like empty feed!')
            return

        for media in feed:
            self._sleep()
            self.like(media)

    # perform a like operation
    def like(self, media):
        """ Send http request to like media by ID """
        if self.bot.login_status:
            print('Liking a {0}'.format(media['media_type']))
            url_likes = self.bot.url_likes % (media['media_id'])
            try:
                like = self.bot.s.post(url_likes)
                self.likes.append(media)
            except:
                print("Like operation failed!")
                like = 0
            return like

    def interact(self, user_name, max_likes=5, max_followers=5, comment_rate=.1):
        user_feed = self.get_feed(user_name, max_likes)
        self.feed_liker(user_feed)

        followers = self.get_user_followers(user_name, max_followers)
        for follower in followers:
            feed = self.get_feed(follower['username'], max_likes)
            self.feed_liker(feed)

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
