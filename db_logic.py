import sqlalchemy as db
from sqlalchemy.orm import sessionmaker

from models import create_tables, Viewed, ProfileInfo


class DBLogic:
    def __init__(self):
        self.engine = db.create_engine('sqlite:///VKinder.db')
        create_tables(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def __del__(self):
        self.session.close()

    # Viewing
    def viewing(self, profile_id, user_id):
        """
        заносит просмотренные id в db
        """
        data = Viewed(profile_id=profile_id,
                      worksheet_id=user_id)
        self.session.add(data)
        self.session.commit()

    def getting_verified_all_id(self, profile_id):
        """
        выводит список всех проверенных id данным пользователем
        """
        verified_all_id = [k[0] for k in self.session.query(Viewed.worksheet_id).filter(Viewed.profile_id == str(profile_id)).all()]
        return verified_all_id

    def getting_verified_id(self, profile_id, user_id):
        """
        проверяет, просматривал ли данный пользователь этого человека:
        """
        answer = self.session.query(Viewed).filter(Viewed.profile_id == str(profile_id),
                                                   Viewed.worksheet_id == str(user_id)).first()
        return bool(answer)

    # ProfileInfo
    def recording_profile_info(self, params):
        """
        заносит данных пользователя в db
        """
        data = ProfileInfo(profile_id=params['id'],
                           profile_name=params['name'],
                           profile_bdate=params['bdate'],
                           profile_sex=params['sex'],
                           profile_city=params['city'])
        self.session.add(data)
        self.session.commit()

    def getting_profile_info(self, profile_id):
        """
        получение данных пользователя
        """
        profile_info = self.session.query(ProfileInfo).filter(ProfileInfo.profile_id == str(profile_id)).first()
        return profile_info

    def update_profile_info(self, id, parameter, value):
        """
        изменение персональных данных
        """
        up_pi = self.session.query(ProfileInfo).get(id)
        if parameter == 'profile_bdate':
            up_pi.profile_bdate = value
        elif parameter == 'profile_sex':
            up_pi.profile_sex = value
        elif parameter == 'profile_city':
            up_pi.profile_city = value
        self.session.add(up_pi)
        self.session.commit()

