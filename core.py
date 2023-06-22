import vk_api
from datetime import datetime


from config import acces_token

class VkTools:
    def __init__(self, acces_token):
       self.api = vk_api.VkApi(token=acces_token)

    def get_profile_info(self, user_id):

        info, = self.api.method('users.get', {'user_id': user_id,
                                             'fields': 'city,bdate,sex,relation,home_town'}
                               )
        user_info = {'name': f"{info['first_name']} {info['last_name']}",
                     'id': info['id'],
                     'bdate': info.get('bdate'),
                     'sex': info.get('sex'),
                     'city_name': info['city']['title'],
                     'city_id': info['city']['id'],
                     }
        return user_info

    def formation_search_terms(self, params):
        """
        формирование условий поиска
        """
        age = datetime.now().year - int(params['bdate'].split('.')[2])  # исправить, так как будет выдавать ошибку
        search_terms = {'count': 1000,
                        'offset': 0,
                        'age_from': age - 5,
                        'age_to': age + 5,
                        'sex': 1 if params['sex'] == 2 else 2,
                        'city': params['city_id'],
                        'status': 6,
                        'is_closed': False}
        return search_terms

    def serch_users(self, search_terms):
        users = self.api.method('users.search', search_terms)
        return users['items'] if users.get('items') is not None else []

    def get_photos(self, photos):
        """
        получение фотографий пользователя из профеля
        """
        photos = sorted(photos, key=lambda x: x['likes']['count']+x['comments']['count'], reverse=True)[0:3]
        attachment = [photo['sizes'][-1]['url'] for photo in photos]
        attachment = []  # для тестов
        return ', '.join(attachment)

    def enumeration_found_users(self, users):
        user = users.pop()
        return user

    def data_acquisition_user(self, user):
        if user['can_access_closed']:
            get_photos = self.api.method('photos.get',
                                     {'owner_id': user['id'],
                                      'album_id': 'profile',
                                      'extended': 1
                                      }
                                     )
            if get_photos['count'] > 0:
                user_name = f"{user['first_name']} {user['last_name']}"
                attachment = self.get_photos(get_photos['items'])
                print(user_name, attachment)
                return user['id'], user_name, attachment
        return user['id'], None, None

    def city_id(self, name):
        name = name.split(', ')
        city = self.api.method('database.getCities',
                               {'q': {name[0]},
                                'need_all': 0})
        if city['count'] == 0:
            return None, None
        print(city)
        if len(name) > 1:
            for c in city['items']:
                if c.get('region') == name[1].capitalize():
                    return name[0], c['id']
        return name[0], city['items'][0]['id']
