#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
import json
from surebot import SureBot

myBot = SureBot('mofesolapaul', 'Adebanke1.')

# print(myBot.get_feed('somebody_i_love1', max_followers=2))
myBot.interact('ajadi', max_followers=0, max_likes=1)
myBot.die()
