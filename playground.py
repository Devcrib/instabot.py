#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
import json
from surebot import SureBot

myBot = SureBot('mofesolapaul', 'Adebanke1.')

print(myBot.get_user_followers('somebody_i_love1', max_followers=2))
