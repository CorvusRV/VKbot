import vk_api
import re
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from config import comunity_token, acces_token
from core import VkTools
from db_logic import DBLogic
from help import help


class BotInterface:
    def __init__(self, comunity_token, acces_token):
        self.interface = vk_api.VkApi(token=comunity_token)
        self.api = VkTools(acces_token)
        self.db_logic = DBLogic()  # управление базой данных
        self.longpoll = VkLongPoll(self.interface)
        self.params = None
        self.search_terms = None
        self.offset = 0

    def message_send(self, user_id, text, attachment=None):
        self.interface.method('messages.send',
                              {'user_id': user_id,
                               'message': text,
                               'attachment': attachment,
                               'random_id': get_random_id()}
                              )

    def request_for_data_user(self):  # переделать цикл
        user_name = None
        print(self.offset)
        users = self.api.search_users(self.search_terms, self.offset)
        while user_name is None:
            user = self.api.enumeration_found_users(users)
            self.offset += 1
            if not self.db_logic.getting_verified_id(self.params['id'], user['id']):
                user_id, user_name, attachment = self.api.data_acquisition_user(user)
                self.db_logic.viewing(self.params['id'], user_id)
        return user_id, user_name, attachment

    def list_liked_users(self):
        """
        запрашивает id понравившихся пользователей и формирует ссылки на их аккаунты
        """
        list_users_id = self.db_logic.getting_list_liked_users_id(self.params['id'])
        list_liked_users = [f'https://vk.com/id{user_id}' for user_id in list_users_id]
        return '\n'.join(list_liked_users)

    def event_handler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                command = event.text.lower()
                if command in ('привет', 'старт'):  # стартовая команда
                    if self.params is None:
                        self.params = self.api.get_profile_info(event.user_id)
                    self.message_send(event.user_id, f'Здравствуте {self.params["name"]}')

                    # проверка данных пользователя
                    if self.params['bdate'] is None:
                        self.message_send(event.user_id, 'Введите дату рождения ДД.ММ.ГГГГ')
                        for event in self.longpoll.listen():
                            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                                bdate = event.text.lower()
                                if re.search(r'\d\d.\d\d.\d{4}', bdate):
                                    self.params['dbase'] = bdate
                                    self.message_send(event.user_id, 'Дата рождения принята')
                                    break
                                self.message_send(event.user_id, 'Попробуйте еще раз')
                    if self.params['sex'] is None:
                        self.message_send(event.user_id, 'Введите свой пол м/ж')
                        for event in self.longpoll.listen():
                            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                                sex = event.text.lower()
                                if sex == 'м' or sex == 'ж':
                                    self.params['sex'] = 1 if sex == 'ж' else 2
                                    self.message_send(event.user_id, 'Пол принят')
                                    break
                                self.message_send(event.user_id, 'Попробуйте еще раз')
                    if self.params['city_id'] is None:
                        self.message_send(event.user_id, 'Введите название вашего города проживания.\n'
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
                                self.message_send(event.user_id, 'Попробуйте еще раз')

                # команды для проверки личных данных
                elif command == 'мои данные' and self.params is not None:  # проверка данных клиента
                    self.message_send(event.user_id, f"name: {self.params['name']}\n"
                                                     f"id: {self.params['id']}\n"
                                                     f"bdate: {self.params['bdate']}\n"
                                                     f"sex: {'ж' if self.params['sex'] == 1 else 'м'}\n"
                                                     f"city: {self.params['city_name']}")
                # команды для поиска людей и проверки условий поиска
                elif command == 'условия поиска' and self.params is not None:  # проверка условий поиска
                    if self.search_terms is None:
                        self.search_terms = self.api.formation_search_terms(self.params)
                    self.message_send(event.user_id, f"age: {self.search_terms.get('age_from')} - {self.search_terms.get('age_to')}\n"
                                                     f"sex: {self.search_terms.get('sex')}\n"
                                                     f"city: {self.search_terms.get('city_name')}")
                # команды для изменнений условий поиска
                elif re.search(r'поиск по возрасту - \d{2,3}-\d{2,3}$', command) and self.search_terms is not None:
                    age = command.split(' - ')
                    age_from, age_to = age[1].split('-')
                    self.search_terms['age_from'], self.search_terms['age_to'] = int(age_from), int(age_to)
                    self.message_send(event.user_id, f"age: {self.search_terms.get('age_from')} - {self.search_terms.get('age_to')}")
                elif re.search(r'поиск по полу - [12]{1}', command) and self.search_terms is not None:  # воспринимает 1,2,12,21 исправить
                    sex = command.split()[4]
                    self.search_terms['sex'] = sex
                    self.message_send(event.user_id, f"sex: {self.search_terms.get('sex')}")
                elif re.search(r'поиск по городу - \w', command) and self.search_terms is not None:
                    city = command.split(' - ')[1]
                    city_id, city_name = self.api.city_id(city)
                    if city_id is not None:
                        self.search_terms['city_id'] = city_id
                        self.search_terms['city_name'] = city_name.capitalize()
                        self.message_send(event.user_id, f"city_id: {self.search_terms['city_name']}")
                    else:
                        self.message_send(event.user_id, "Попробуй еще раз")
                elif command == 'поиск' and self.params is not None:
                    if self.search_terms is None:
                        self.search_terms = self.api.formation_search_terms(self.params)
                    user_id, user_name, attachment = self.request_for_data_user()
                    self.message_send(event.user_id, f'Встречайте {user_name}'
                                                     f'\nhttps://vk.com/id{user_id}', attachment=attachment)
                elif command == 'нравится' and self.params is not None:
                    self.db_logic.mark_user_like(self.params['id'], user_id)
                    self.message_send(event.user_id, f"{user_id}")
                elif command == 'сбросить условия поиска':
                    self.search_terms = None  # для избежания случайных ошибок
                elif command == 'понравившиеся' and self.params is not None:
                    list_liked_users = self.list_liked_users()
                    self.message_send(event.user_id, f'{list_liked_users}')
                elif re.search(r'проверить - \d', command):  # доделать команду
                    user_id = command.split(' - ')[1]
                    get = self.db_logic.getting_verified_id(self.params['id'], user_id)
                    self.message_send(event.user_id, f'пользователь {user_id} проверяется {get}')
                elif command == 'помощь':  # данная команда выводит все команды
                    self.message_send(event.user_id, help)
                elif command == 'пока':
                    self.message_send(event.user_id, 'пока')
                else:
                    self.message_send(event.user_id, 'Я вас не понимаю!')



if __name__ == '__main__':
    bot = BotInterface(comunity_token, acces_token)
    bot.event_handler()
