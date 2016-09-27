# coding:utf-8:

import os
import re
import pickle
import subprocess

from twx.botapi import InputFileInfo, InputFile

import sound
from controller import Controller

from lisp.sexpressions import (
         SexprBuiltin, SexprProcedure, SexprNil,
         car, cdr, consp, symbol_name, is_callable,
         intern_symbol, string_value, SexprSymbol,
         is_keyword,
     )
from lisp.parser import Parser
from lisp.evaluator import (
         global_environment, eval_expression, env_keys, rib_keys,
         env_lookup, env_define, env_set,
     )
from lisp.persistence import (env_dump, env_load)

IMAGE_FN = '_lisp_image.txt'

class LispController(Controller):

    def __init__(self, bot):
        self._basic_messages = ['eval']
        super(LispController, self).__init__(bot, self._basic_messages)
        self._environment = global_environment()
        self._install_image()
        self._install_sound()
        self._image_load()

    def handle_update(self, update):
        contents = update.message.text.split(' ')
        contents[0] = contents[0].split('@')[0]
        command = contents[0]
        contents = ' '.join(contents)
        self._last_update = update
        for message in self._basic_messages: 
            if contents == '/' + message or contents.startswith('/' + message + ' '):
                getattr(self, message)(update)
                return True
        if command[1:] in self.messages():
            self._eval_text('(' + contents[1:] + ')', update.message.chat.id)
            return True
        return False

    def eval(self, update):
        try:
            contents = update.message.text
            contents = contents.split(' ')
            if len(contents) <= 1:
                return
            contents = ' '.join(contents[1:])
            self._eval_text(contents, update.message.chat.id, silent=False)
        except Exception as e:
            self._bot.send_message(update.message.chat.id, 'Error: ' + e.message)

    def _eval_text(self, contents, chat_id, silent=True):
        try:
            result = eval_expression(
                       Parser(contents).parse_expression(),
                       self._environment)
            if not silent or result != SexprNil():
                self._bot.send_message(chat_id, repr(result))
        except Exception as e:
            self._bot.send_message(chat_id, 'Error: ' + e.message)

    def _image_load(self):
        if os.path.exists(IMAGE_FN):
            f = file(IMAGE_FN, 'r')
            elements = pickle.load(f)
            f.close()
            env_load(self._environment, elements)
            print('imagen cargada')

    def _image_dump(self):
        f = file(IMAGE_FN, 'w')
        pickle.dump(env_dump(self._environment), f)
        f.close()

    def messages(self):
        available = {}
        special_forms = ['def', 'let', 'let*', 'fun', 'if', 'do', 'quote', 'set']
        for s in special_forms:
            available[s] = True
        for key in env_keys(self._environment):
            if is_callable(env_lookup(self._environment, key)):
                available[symbol_name(key)] = True
        return sorted(available.keys())
 
    def help_message(self):
        return u'''
/eval expresion : evalúa la expresión
'''

    def _install_image(self):
        env_define(self._environment,
                   intern_symbol('save'),
                   SexprBuiltin('save', self._save))

    def _save(self, environment):
        try:
            print('imagen guardada')
            self._image_dump()
            return intern_symbol('*imagen-guardada*')
        except Exception as e:
            print('error al guardar la imagen')
            print(e)
            return intern_symbol('*error-al-guardar-la-imagen*')

    def _install_sound(self):
        env_define(self._environment,
                   intern_symbol('play'),
                   SexprBuiltin('play', self._play))
        env_define(self._environment,
                   intern_symbol('talk'),
                   SexprBuiltin('talk', self._talk))

    def _play(self, environment, string):
        sound.play(string_value(string))
        f = open('_tmp_.ogg', 'r')
        file_info = InputFileInfo('_tmp_.ogg', f, 'audio/ogg')
        input_file = InputFile('voice', file_info)
        self._bot.send_voice(self._last_update.message.chat.id, input_file)
        return SexprNil()

    def _talk(self, environment, string, language=None):
        if language is None:
            language = 'es'
        elif isinstance(language, SexprSymbol):
            if is_keyword(language):
                language = symbol_name(language)[1:]
            else:
                language = symbol_name(language)
        elif isinstance(language, SexprString):
            language = string_value(language)
        else:
            language = 'es'
        text = string_value(string)
        subprocess.call(['/usr/bin/espeak', '-v', language, '-w', '_tmp_.wav', text])
        os.system('oggenc _tmp_.wav')
        f = open('_tmp_.ogg', 'r')
        file_info = InputFileInfo('_tmp_.ogg', f, 'audio/ogg')
        input_file = InputFile('voice', file_info)
        self._bot.send_voice(self._last_update.message.chat.id, input_file)
        return SexprNil()

