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

    def getting_list_liked_users_id(self, profile_id):
        """
        выводит список id всех понравившихся партнеров
        """
        list_liked_users_id = [k[0] for k in self.session.query(Viewed.worksheet_id).filter(
            Viewed.profile_id == str(profile_id), Viewed.like == str(1)).all()]
        return list_liked_users_id

    def getting_verified_id(self, profile_id, user_id):
        """
        проверяет, просматривал ли данный пользователь этого человека
        """
        answer = self.session.query(Viewed).filter(Viewed.profile_id == str(profile_id),
                                                   Viewed.worksheet_id == str(user_id)).first()
        return bool(answer)

    def mark_user_like(self, profile_id, worksheet_id):
        """
        отмечает человека, как понравившегося
        """
        print(profile_id, worksheet_id)
        user_like = self.session.query(Viewed).get([profile_id, worksheet_id])
        user_like.like = True
        self.session.add(user_like)
        self.session.commit()go

