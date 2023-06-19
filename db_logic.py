import sqlalchemy as db
from sqlalchemy.orm import sessionmaker

from models import create_tables, Viewed


class DBLogic:
    def __init__(self):
        self.engine = db.create_engine('sqlite:///shows.db')
        create_tables(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def __del__(self):
        self.session.close()

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

