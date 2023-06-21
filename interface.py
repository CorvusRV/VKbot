import vk_api
import re
from vk_api.longpoll import VkLongPoll, VkEventType

from config import comunity_token, acces_token
from core import VkTools
from db_logic import DBLogic


class BotInterface:
    def __init__(self, comunity_token, acces_token):
        self.interface = vk_api.VkApi(token=comunity_token)
        self.api = VkTools(acces_token)
        self.db_logic = DBLogic()  # управление базой данных
        self.params = None
        self.search_terms = None

    def message_send(self, user_id, text):
        self.interface.method('messages.send',
                              {'user_id': user_id,
                               'message': text,
                               'random_id': 0}
                              )

    def request_for_data_user(self):
        users = self.api.serch_users(self.search_terms)
        user_name = None
        while user_name is None:
            user = self.api.enumeration_found_users(users)
            if not self.db_logic.getting_verified_id(self.params['id'], user['id']):
                user_id, user_name, attachment = self.api.data_acquisition_user(user)
                self.db_logic.viewing(self.params['id'], user_id)
        return user_id, user_name, attachment

    def event_handler(self):
        longpoll = VkLongPoll(self.interface)

        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                command = event.text.lower()

                if command == 'привет':  # стартовая команда
                    params = self.db_logic.getting_profile_info(event.user_id)
                    if params is None:
                        self.params = self.api.get_profile_info(event.user_id)
                        self.db_logic.recording_profile_info(self.params)  # внесение данных в db, для дальнейшей работы
                    else:
                        self.params = {'name': params.profile_name,
                                       'id': params.profile_id,
                                       'bdate': params.profile_bdate,
                                       'sex': params.profile_sex,
                                       'city': params.profile_city}
                    self.message_send(event.user_id, f'Здравствуй {self.params["name"]}')
                    client_info = self.api.checking_client_info(self.params)
                    if client_info:
                        self.message_send(event.user_id, client_info)

                # команды для проверки личных данных и их изменения
                elif command == 'мои данные' and self.params is not None:  # проверка данных клиента
                    self.message_send(event.user_id, f"name: {self.params.get('name')}\n"
                                                     f"id: {self.params.get('id')}\n"
                                                     f"bdate: {self.params.get('bdate')}\n"
                                                     f"sex: {self.params.get('sex')}\n"
                                                     f"city_id: {self.params.get('city')}")
                # команды для изменений личных данных, которых изначально может не оказаться
                elif re.search(r'дата рождения - \d\d.\d\d.\d{4}', command) and self.params is not None:
                    bdate = command.split()[3]
                    self.params['bdate'] = bdate
                    self.db_logic.update_profile_info(self.params['id'], 'profile_bdate', self.params['bdate'])
                    self.message_send(event.user_id, f'Дата рождения {bdate} принята')
                elif re.search(r'пол - [12]{1}', command) and self.params is not None:  # воспринимает 1,2,12,21 исправить
                    sex = command.split()[2]
                    self.params['sex'] = sex
                    self.db_logic.update_profile_info(self.params['id'], 'profile_sex', self.params['sex'])
                    self.message_send(event.user_id, f'Пол принят')
                elif re.search(r'город - \w', command) and self.params is not None:  # воспринимает 1,2,12,21 исправить
                    name = command.split(' ', 2)[2]
                    name, self.params['city'] = self.api.city_id(name)
                    self.db_logic.update_profile_info(self.params['id'], 'profile_city', self.params['city'])
                    self.message_send(event.user_id, f"Город {name}, id = {self.params['city']}")
                # команды для поиска людей и проверки условий поиска
                elif command == 'условия поиска' and self.params is not None:  # проверка условий поиска
                    if self.search_terms is None:
                        self.search_terms = self.api.formation_search_terms(self.params)
                    self.message_send(event.user_id, f"age: {self.search_terms.get('age_from')} - {self.search_terms.get('age_to')}\n"
                                                     f"sex: {self.search_terms.get('sex')}\n"
                                                     f"city_id: {self.search_terms.get('city')}")
                # команды для изменнений условий поиска
                elif re.search(r'поиск по возрасту - \d{2,3} - \d{2,3}', command) and self.search_terms is not None:
                    age = command.split(' - ')
                    self.search_terms['age_from'] = int(age[1])
                    self.search_terms['age_to'] = int(age[2])
                    self.message_send(event.user_id, f"age: {self.search_terms.get('age_from')} - {self.search_terms.get('age_to')}")
                elif re.search(r'поиск по полу - [12]{1}', command) and self.search_terms is not None:  # воспринимает 1,2,12,21 исправить
                    sex = command.split()[4]
                    self.search_terms['sex'] = sex
                    self.message_send(event.user_id, f"sex: {self.search_terms.get('sex')}")
                elif re.search(r'поиск по городу - \w', command) and self.search_terms is not None:  # воспринимает 1,2,12,21 исправить
                    name = command.split(' ', 4)[4]
                    name, self.search_terms['city'] = self.api.city_id(name)
                    self.message_send(event.user_id, f"city_id: {self.search_terms.get('city')}")
                elif command == 'поиск' and self.params is not None:
                    if self.search_terms is None:
                        self.search_terms = self.api.formation_search_terms(self.params)
                    user_id, user_name, attachment = self.request_for_data_user()
                    self.message_send(event.user_id,
                                      f"Встречайте {user_name}\nhttps://vk.com/id{user_id}\n\n{attachment}")
                elif command == 'следующий':
                    user_id, user_name, attachment = self.request_for_data_user()
                    self.message_send(event.user_id,
                                      f"Встречайте {user_name}\nhttps://vk.com/id{user_id}\n\n{attachment}")
                elif command == 'сбросить данные поиска':  # формирует уловия поиска, относительно параметров клиента
                    self.search_terms = self.api.formation_search_terms(self.params)
                elif command == 'просмотренные':
                    verified_all_id = self.db_logic.getting_verified_all_id(self.params['id'])
                    self.message_send(event.user_id, f'{verified_all_id}')
                elif re.search(r'проверить - \d', command):
                    user_id = command.split(' - ')[1]
                    get = self.db_logic.getting_verified_id(self.params['id'], user_id)
                    self.message_send(event.user_id, f'пользователь {user_id} проверяется {get}')
                elif command == 'помощь':  # данная команда выводит все команды
                    self.message_send(event.user_id, f'Извини, команда не работает, она должна выводить подсказку по командам')
                elif command == 'пока':
                    self.message_send(event.user_id, 'пока')
                else:
                    self.message_send(event.user_id, 'Я вас не понимаю! :(')



if __name__ == '__main__':
    bot = BotInterface(comunity_token, acces_token)
    bot.event_handler()
