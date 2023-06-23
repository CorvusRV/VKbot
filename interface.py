import vk_api
import re
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from config import comunity_token, acces_token
from core import VkTools
from db_logic import DBLogic
from command_help import command_help


command_not_recognized = 'Команда не распознана'
user_id = None
class BotInterface:
    def __init__(self, comunity_token, acces_token):
        self.interface = vk_api.VkApi(token=comunity_token)
        self.api = VkTools(acces_token)
        self.db_logic = DBLogic()  # управление базой данных
        self.longpoll = VkLongPoll(self.interface)
        self.params = {None}
        self.search_terms = None

    def message_send(self, user_id, text, attachment=None):
        self.interface.method('messages.send',
                              {'user_id': user_id,
                               'message': text,
                               'attachment': attachment,
                               'random_id': get_random_id()}
                              )

    def event_handler(self):
        user_id = None
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                command = event.text.lower()
                if command == 'старт':
                    if self.params is None:
                        self.params = self.api.get_profile_info(event.user_id)
                    self.message_send(event.user_id, f'Здравствуте {self.params["name"]}')

                    # проверка данных пользователя
                    if re.search(r'^\d{1,2}.\d{1,2}.\d{4}$', str(self.params['bdate'])) is None:
                        self.message_send(event.user_id, 'Введите дату рождения ДД.ММ.ГГГГ')
                        for event in self.longpoll.listen():
                            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                                bdate = event.text.lower()
                                if re.search(r'^\d{1,2}.\d{1,2}.\d{4}$', bdate):
                                    self.params['dbase'] = bdate
                                    self.message_send(event.user_id, 'Дата рождения принята')
                                    break
                                self.message_send(event.user_id, command_not_recognized)
                    if self.params['sex'] is None:
                        self.message_send(event.user_id, 'Введите пол м/ж')
                        for event in self.longpoll.listen():
                            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                                command = event.text.lower()
                                if re.search(r'^[мж]$', command):
                                    self.params['sex'] = 1 if command == 'ж' else 2
                                    self.message_send(event.user_id, 'Пол принят')
                                    break
                                self.message_send(event.user_id, command_not_recognized)
                    if self.params['city_id'] is None:
                        self.message_send(event.user_id, 'Введите название города проживания.\n'
                                                         'Через занятую можно уточнить область.')
                        for event in self.longpoll.listen():
                            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                                city = event.text.lower()
                                city_id, city_name = self.api.city_id(city)
                                if city_id is not None:
                                    self.params['city_id'] = city_id
                                    self.params['city_name'] = city_name.capitalize()
                                    self.message_send(event.user_id, f"Город {self.params['city_name']} принят")
                                    break
                                self.message_send(event.user_id, command_not_recognized)

                elif command == 'поиск' and self.params is not None:
                    if self.search_terms is None:
                        self.search_terms = self.api.formation_search_terms(self.params)
                    user_id, user_name, attachment = self.api.request_for_data_user(event.user_id, search_terms=self.search_terms)
                    self.message_send(event.user_id, f'Встречайте {user_name}'
                                                     f'\nhttps://vk.com/id{user_id}', attachment=attachment)
                elif command == 'нравится' and self.params is not None and user_id is not None:  # исправить ошибку, которая возникнет, если написать нравится до поиска
                        self.db_logic.mark_user_like(self.params['id'], user_id)
                        self.message_send(event.user_id, f"Пользователь отмечен")
                elif command == 'понравившиеся':
                    list_liked_users = self.db_logic.getting_list_liked_users(event.user_id)
                    self.message_send(event.user_id, f'{list_liked_users}')

                # команды для проверки личных данных
                elif command == 'мои данные' and self.params is not None:  # проверка данных клиента
                    self.message_send(event.user_id, f"Идентификатор: {self.params['id']}\n"
                                                     f"Имя: {self.params['name']}\n"
                                                     f"Дата рождения: {self.params['bdate']}\n"
                                                     f"Пол: {'ж' if self.params['sex'] == 1 else 'м'}\n"
                                                     f"Город: {self.params['city_name']}")
                # команды проверки и изменения условий поиска
                elif command == 'условия поиска' and self.params is not None:  # проверка условий поиска
                    if self.search_terms is None:
                        self.search_terms = self.api.formation_search_terms(self.params)
                    self.message_send(event.user_id, f"Возраст: {self.search_terms.get('age_from')} - "
                                                     f"{self.search_terms.get('age_to')}\n"
                                                     f"Пол: {self.search_terms.get('sex')}\n"
                                                     f"Город: {self.search_terms.get('city_name')}")
                elif command == 'изменить условия поиска' and self.search_terms is None:
                    self.message_send(event.user_id, 'Введите возраста партнера в формате ??-??')
                    for event in self.longpoll.listen():
                        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                            command = event.text.lower()
                            if command == 'оставить':
                                break
                            elif re.search(r'^\d{2,3}-\d{2,3}$', command):
                                age_from, age_to = command.split('-')
                                self.search_terms['age_from'] = int(age_from)
                                self.search_terms['age_to'] = int(age_to)
                                self.message_send(event.user_id, f"Возраст: {self.search_terms.get('age_from')}"
                                                                 f"-{self.search_terms.get('age_to')}")
                                break
                            else:
                                self.message_send(event.user_id, command_not_recognized)
                    self.message_send(event.user_id, 'Введите пол партнера м/ж')
                    for event in self.longpoll.listen():
                        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                            command = event.text.lower()
                            if command == 'оставить':
                                break
                            elif re.search(r'^[мж]$', command):
                                self.search_terms['sex'] = 1 if command == 'ж' else 2
                                self.message_send(event.user_id,
                                                  f"Пол: {'ж' if self.search_terms['sex'] == 1 else 'м'}")
                                break
                            else:
                                self.message_send(event.user_id, command_not_recognized)
                    self.message_send(event.user_id, 'Введите город проживания партнера')
                    for event in self.longpoll.listen():
                        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                            command = event.text.lower()
                            if command == 'оставить':
                                break
                            else:
                                city_id, city_name = self.api.city_id(command)
                                if city_id is not None:
                                    self.search_terms['city_id'] = city_id
                                    self.search_terms['city_name'] = city_name.capitalize()
                                    self.message_send(event.user_id,
                                                      f"Город партнера - {self.search_terms['city_name']}")
                                    break
                                self.message_send(event.user_id, command_not_recognized)

                elif command == 'сбросить условия поиска' and self.search_terms is not None:
                    self.search_terms = None
                elif command == 'помощь':
                    self.message_send(event.user_id, command_help)
                else:
                    self.message_send(event.user_id, command_not_recognized)



if __name__ == '__main__':
    bot = BotInterface(comunity_token, acces_token)
    bot.event_handler()
