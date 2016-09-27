# coding:utf-8:
import os
import time
import sys
from twx.botapi import TelegramBot, ReplyKeyboardMarkup

from lisp_controller import LispController
from help_controller import HelpController

sys.setrecursionlimit(1000)
LAST_UPDATE_FN = 'last_update.txt'

def set_last_update(last_update_id):
    f = file(LAST_UPDATE_FN, 'w')
    f.write(str(last_update_id) + '\n')
    f.close()

def get_last_update():
    if os.path.exists(LAST_UPDATE_FN):
        f = file(LAST_UPDATE_FN, 'r')
        line = f.readline()
        f.close()
        return int(line.strip(' \t\r\n'))
    else:
        return -1

class Bot(object):

    def __init__(self, token):
        self._bot = TelegramBot(token)

        self._controllers = [
            LispController(self._bot),
        ]
        self._controllers.append(
            HelpController(self._bot, self._controllers)
        )
        self._bot.update_bot_info().wait()
        print 'ok'

    def poll(self):
        updates = self._bot.get_updates(offset=get_last_update() + 1).wait()
        for update in updates:
            print(update)
            try:
                set_last_update(update.update_id)
                if update.message.text is None:
                    continue
                for controller in self._controllers:
                    if controller.handle_update(update):
                        break
            except Exception as e:
                print(e)
                try:
                    self._bot.send_message(update.message.chat.id,
                                           u'Mensaje inválido men: ' + repr(e))
                except Exception as e:
                    print('inner exception: ' + repr(e))
                    continue

TOKEN = '<token>'
print('Set the bot token on main.py')
sys.exit(1)

bot = Bot(TOKEN)
while True:
    try:
        bot.poll()
    except Exception as e:
        print(e)
    time.sleep(0.2)

