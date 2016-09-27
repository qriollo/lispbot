
class Controller(object):

    def __init__(self, bot, messages):
        self._bot = bot
        self._messages = messages

    def handle_update(self, update):
        for message in self._messages: 
            if update.message.text.startswith('/' + message):
                getattr(self, message)(update)
                return True
        return False

    def messages(self):
        return self._messages

    def name(self):
        name = self.__class__.__name__
        if name.endswith('Controller'):
            name = name[:-len('Controller')]
        return name.lower()

    def help_message(self):
        return '[no help available]'

