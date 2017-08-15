#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function, absolute_import
import json
from surebot import SureBot

myBot = SureBot('mofesolapaul', 'Adebanke1.')

data = myBot.get_user_followers('anike')
if data: print(json.dumps(data))
else: print('toor')
