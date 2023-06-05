import vk_api
from config import comunity_token

class VkTools():
    def __init__(self, comunity_token):
       self.api = vk_api.VkApi(token=comunity_token)

    def get_profile_info(self, user_id):

        info, = self.api.method('users.get', {'user_id': user_id,
                                             'fields': 'city,bdate,sex,relation,home_town'}
                               )
        user_info = {'name': f"{info['first_name']} {info['last_name']}",
                     'id': info['id'],
                     'bdate': info.get('bdate'),
                     'sex': info.get('sex'),
                     'city': info['city']['id']
                     }
        return user_info

if __name__ == '__main__':
    bot = VkTools(comunity_token)
    params = bot.get_profile_info(42275469)
    print(params)
