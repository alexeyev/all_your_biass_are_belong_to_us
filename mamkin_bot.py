# -*- coding: utf-8 -*-
"""
Copyright 2017 Neural Networks and Deep Learning lab, MIPT

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json
import os
import random
from time import sleep

import requests
from lru import LRU

from data_preparation import embed_all_in_dir, find_closest_responses
from log_config import lg

NEIGHBOURS = 5

vectorizer, searcher, pairs = embed_all_in_dir(neighbours_count=NEIGHBOURS)

stoplist = open("stoplist.txt").read().strip().split("\n")

users_letters = "qazwsxedcrfvtgbyhnujmiklop"


class ConvAISampleBot:

    def __init__(self):
        self.chat_id = None
        self.observation = None

    def observe(self, m):
        lg.info("Observe:")
        self.chat_id = m['message']['chat']['id']
        self.observation = m['message']['text']
        lg.info("\tStart new chat #%s" % self.chat_id)
        return self.observation

    def act(self):
        lg.info("Act:")

        if self.chat_id is None:
            lg.info("\tChat not started yet. Do not act.")
            return

        if self.observation is None:
            lg.info("\tNo new messages for chat #%s. Do not act." % self.chat_id)
            return

        message = {
            'chat_id': self.chat_id
        }

        should_finish = random.randint(0, 15) == 0
        data = {}

        if not should_finish:
            lg.info("Responding to " + str(self.observation))

            # superweird stuff, I know
            guess_name = random.randint(0, 2500) == 5

            if guess_name:

                selected_user_name_length = random.randint(3, 7)
                name = ""

                for i in range(selected_user_name_length):
                    name += users_letters[random.randint(0, len(users_letters) - 1)]

                name += " "

                selected_user_name_length = random.randint(3, 7)

                for i in range(selected_user_name_length):
                    name += users_letters[random.randint(0, len(users_letters) - 1)]

                data["text"] = "Are you @" + name.title().replace(" ", "") + " on Telegram?"
            else:
                responses = find_closest_responses(self.observation, vectorizer, searcher, pairs, neighbours_count=NEIGHBOURS)

                if len(responses) > 1:
                    data["text"] = responses[random.randint(0, len(responses) - 1)][1]
                else:
                    data["text"] = responses[0][1]

                lg.info("Prior to obscene filters " + data["text"])

                for sw in stoplist:
                    if sw in data["text"].lower():
                        if random.randint(0, 10) != 0:
                            replies_instead = ["OH my god", "God almighty", "Le me so tired", "I'm tired",
                                               "Please... Let's talk about something else", "Me so tired",
                                               "Imma tired fluffy kitty", "oh deer", "jesus", "jeez", ]
                            data["text"] = replies_instead[random.randint(0, len(replies_instead) - 1)]
                        else:
                            data["text"] = data["text"].lower().replace(sw, "kitty")

                if random.randint(0, 5) == 1:
                    splitter = random.randint(1, len(data["text"]) - 1)
                    data["text"] = data["text"][:splitter] + " " + data["text"][splitter:]

            lg.info("Responding with " + data['text'])
        else:
            lg.info("\tDecide to finish chat " + str(self.chat_id))

            self.chat_id = None
            data['text'] = '/end'

            data['evaluation'] = {
                'quality': 0,
                'breadth': 0,
                'engagement': 0
            }

        message['text'] = json.dumps(data)
        return message


def main():

    BOT_ID = open("bot_id.conf", "r").read().strip()

    if BOT_ID is None:
        raise Exception('You should enter your bot token/id!')

    BOT_URL = os.path.join('https://ipavlov.mipt.ru/nipsrouter/', BOT_ID)

    # todo: better way to store sessions, not in RAM
    bot_map = LRU(55)

    while True:
        try:
            lg.info("Get updates from server")
            res = requests.get(os.path.join(BOT_URL, 'getUpdates'))

            if res.status_code != 200:
                lg.info(res.text)
                res.raise_for_status()

            lg.info("Got %s new messages " + str(len(res.json())))

            for m in res.json():

                lg.info("Process message " + str(m))

                if not m['message']['chat']['id'] in bot_map:
                    lg.info("Chat id is Not in bot map")
                    bot = ConvAISampleBot()
                    bot_map[m['message']['chat']['id']] = bot
                else:
                    lg.info("Chat id is found in bot map")
                    bot = bot_map[m['message']['chat']['id']]

                bot.observe(m)
                new_message = bot.act()

                if new_message is not None:

                    lg.info("Send response to server.")
                    res = requests.post(os.path.join(BOT_URL, 'sendMessage'),
                                        json=new_message,
                                        headers={'Content-Type': 'application/json'})
                    if res.status_code != 200:
                        lg.info(res.text)
                        res.raise_for_status()
            sleep(1)
        except Exception as e:
            lg.exception(e)
            lg.info("Exception: {}".format(e))


if __name__ == '__main__':
    main()
