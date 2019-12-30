import sqlalchemy as db
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from secure import DB_URI

Base = declarative_base()

engine = db.create_engine(DB_URI)
connection = engine.connect()
metadata = db.MetaData()

Session = sessionmaker(bind=engine)


class Entry(Base):
    __tablename__ = 'entry'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    title = Column(String)
    link = Column(String, primary_key=True, unique=True)


class Feed(Base):
    __tablename__ = 'feed'
    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    link = Column(String, primary_key=True)


class Chat(Base):
    __tablename__ = 'chat'
    id = Column(Integer, primary_key=True, unique=True)
