import sqlalchemy as sq
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import Session

Base = declarative_base()


class Viewed(Base):
    __tablename__ = 'viewed'

    profile_id = sq.Column(sq.Integer, primary_key=True)
    worksheet_id = sq.Column(sq.Integer, primary_key=True)

    def __str__(self):
        return f"{self.profile_id}: {self.worksheet_id}"


def create_tables(engine):
    #Base.metadata.drop_all(engine)  # удаление всех существующих таблиц
    Base.metadata.create_all(engine)  # создание всех существующих таблиц