import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

from config import comunity_token
from core import VkTools


class BotInterface():
    def __init__(self, comunity_token):
        self.interface = vk_api.VkApi(token=comunity_token)

    def message_send(self, user_id, text):
        self.interface.method('messages.send',
                              {'user_id' : user_id,
                               'message' : text,
                               'random_id': 0}
                              )

    def event_handler(self):
        longpoll = VkLongPoll(self.interface)

        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                command = event.text.lower()

                if command == 'привет':
                    self.message_send(event.user_id, 'Привет, я бот!')
                elif command == 'как дела?':
                    self.message_send(event.user_id, 'Хорошо, а твои как?')
                else:
                    self.message_send(event.user_id, 'Я вас не понимаю! :(')


if __name__ == '__main__':
    bot = BotInterface(comunity_token)
    bot.event_handler()
# bh = vk_api.VkApi(token=comunity_token)
# give = bh.get_api()
# longpoll = VkLongPoll(bh)
#
#
# def blasthack(id, text):
#     bh.method('messages.send', {'user_id' : id, 'message' : text, 'random_id': 0})
#
# for event in longpoll.listen():
#     if event.type == VkEventType.MESSAGE_NEW:
#         if event.to_me:
#             message = event.text.lower()
#             id = event.user_id
#
#             if message == 'привет':
#                 blasthack(id, 'Привет, я бот!')
#
#             elif message == 'как дела?':
#                 blasthack(id, 'Хорошо, а твои как?')
#
#             else:
#                 blasthack(id, 'Я вас не понимаю! :(')