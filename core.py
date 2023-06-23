import vk_api
from datetime import datetime
from db_logic import DBLogic


class VkTools:
    def __init__(self, acces_token):
        self.api = vk_api.VkApi(token=acces_token)
        self.db_logic = DBLogic()  # управление базой данных
        self.offset = 0

    def get_profile_info(self, user_id):

        info, = self.api.method('users.get', {'user_id': user_id,
                                             'fields': 'city,bdate,sex,relation'})
        user_info = {'name': f"{info['first_name']} {info['last_name']}",
                     'id': info['id'],
                     'bdate': info.get('bdate'),  # может возникнуть ошибка в связи с тем, что скрыт год, необходима проверка (можно вцелом переделать поле на возраст)
                     'sex': info.get('sex'),
                     'city_name': info.get('city')['title'],
                     'city_id': info.get('city')['id'],
                     }
        return user_info

    def formation_search_terms(self, params):
        """
        формирование условий поиска
        """
        age = datetime.now().year - int(params['bdate'].split('.')[2])  # исправить, так как будет выдавать ошибку
        search_terms = {'count': 50,
                        'age_from': age - 5,
                        'age_to': age + 5,
                        'sex': 1 if params['sex'] == 2 else 2,
                        'city': params['city_id'],
                        'city_name': params['city_name'],
                        'status': 6,
                        'is_closed': False}
        return search_terms



    def get_photos(self, photos):
        """
        получение фотографий пользователя из профеля
        """
        photos = sorted(photos, key=lambda x: x['likes']['count']+x['comments']['count'], reverse=True)[0:3]
        attachment = [f'photo{photo["owner_id"]}_{photo["id"]}' for photo in photos]
        return ','.join(attachment)

    def enumeration_found_users(self, users):
        user = users.pop()
        return user

    def data_acquisition_user(self, user_id):
        attachment = None
        photos = self.api.method('photos.get', {'owner_id': user_id,
                                                'album_id': 'profile',
                                                'extended': 1})
        if photos['count'] > 0:
            photos = sorted(photos['items'], key=lambda x: x['likes']['count'] + x['comments']['count'],
                            reverse=True)[0:3]
            attachment = ','.join([f'photo{photo["owner_id"]}_{photo["id"]}' for photo in photos])
        return attachment

    def search_users(self, search_terms):
        search_terms['offset'] = self.offset
        users = self.api.method('users.search', search_terms)
        return users['items'] if users.get('items') is not None else []

    def request_for_data_user(self, params_id, search_terms):
        user_name = None
        attachment = None
        users = self.search_users(search_terms)
        while user_name is None:
            if users is False:
                users.extend(self.search_users(search_terms))
            user = users.pop()
            user_id = user['id']
            self.offset += 1
            if not self.db_logic.getting_verified_id(params_id, user_id):
                self.db_logic.viewing(params_id, user_id)
                if user['can_access_closed']:
                    user_name = f"{user['first_name']} {user['last_name']}"
                    attachment = self.data_acquisition_user(user_id)
        return user_id, user_name, attachment

    def city_id(self, name):
        name = name.split(', ')
        city = self.api.method('database.getCities',
                               {'q': {name[0]},
                                'need_all': 0})
        if city['count'] == 0:
            return None, None
        if len(name) > 1:
            for c in city['items']:
                if c.get('region') == name[1].capitalize():
                    return c['id'], name[0]
        return city['items'][0]['id'], name[0]
