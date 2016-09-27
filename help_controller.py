# coding:utf-8:

from twx.botapi import InputFileInfo, InputFile

import re
from controller import Controller
import sound

class HelpController(Controller):

    def __init__(self, bot, controllers):
        super(HelpController, self).__init__(bot, ['help'])
        self._controllers = controllers

    def help(self, update):
        try:
            text = update.message.text
            text = re.sub('[ \t\r\n]+', ' ', text)
            parts = text.split(' ')
            if len(parts) > 1:
                controller = self._get_controller(parts[1])
            else:
                controller = self
            self._bot.send_message(update.message.chat.id, controller.help_message())
        except Exception as e:
            self._bot.send_message(update.message.chat.id, u'Comando inválido: ' + str(e))

    def _get_controller(self, name):
        for controller in self._controllers:
            if controller.name() == name or \
               name in controller.messages() or \
               (name.startswith('/') and name[1:] in controller.messages()):
                return controller
        return self

    def help_message(self):
        msg = ''
        for controller in sorted(self._controllers, key=lambda c: c.name()):
            msg += '    ' + controller.name() + \
                   ' (' + \
                   ' '.join(sorted(['/' + m for m in controller.messages()])) + \
                   ')\n'
        return u'/help cosa : muestra la ayuda del módulo o comando indicado\n' + \
               u'Módulos y comandos disponibles:\n' + \
               msg

