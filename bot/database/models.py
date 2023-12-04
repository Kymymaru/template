from sqlalchemy import Column, Integer, BigInteger, Text, String, Date, DateTime, JSON, SmallInteger, Float

from .base import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, primary_key=True, unique=True, autoincrement=False)
    ref = Column(Text)
    name = Column(Text)
    username = Column(Text)
    lang_code = Column(String(3))
    status = Column(Integer)
    reg_date = Column(Date)
    death_date = Column(Date)
    last_activity = Column(DateTime)


class Chat(Base):
    __tablename__ = 'chats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, primary_key=True, unique=True)
    title = Column(Text)
    ref = Column(Text)
    status = Column(Integer)
    reg_date = Column(Date)
    death_date = Column(Date)
    data = Column(JSON, default={})


class Bill(Base):
    __tablename__ = 'bills'

    bill_id = Column(BigInteger, primary_key=True, autoincrement=True)
    amount = Column(Integer)
    user_id = Column(BigInteger)
    ref = Column(String(50))
    bill_date = Column(Date)


class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger)
    title = Column(Text)
    is_bot = Column(Integer)
    link = Column(Text)
    status = Column(Integer, default=1)
    users = Column(JSON, default=[])


class Mailing(Base):
    __tablename__ = 'mailing'

    id = Column(BigInteger, autoincrement=True, primary_key=True)
    count = Column(Integer)
    chat_id = Column(BigInteger)
    message_id = Column(BigInteger)
    keyboard = Column(JSON)

    speed = Column(SmallInteger)
    start = Column(Integer)
    mailing_count = Column(Integer)
    mailing_limit = Column(Integer)
    result = Column(JSON)


class Settings(Base):
    __tablename__ = 'settings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    order = Column(SmallInteger)
    count = Column(Integer)
    chat_id = Column(BigInteger)
    message_id = Column(BigInteger)
    keyboard = Column(JSON)


class Show(Base):
    __tablename__ = 'shows'

    id = Column(Integer, autoincrement=True, primary_key=True)
    text = Column(Text)
    file_id = Column(Text)
    file_type = Column(Text)
    keyboard = Column(JSON)
    sent = Column(Integer, default=0)
    need_to_sent = Column(Integer)
    status = Column(Integer, default=1)
    users = Column(JSON, default=[])


class Ref(Base):
    __tablename__ = 'refs'

    id = Column(Integer, autoincrement=True, primary_key=True)
    ref = Column(Text)
    price = Column(Integer, default=0)

