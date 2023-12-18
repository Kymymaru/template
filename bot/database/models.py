import datetime

from aiogram import types
from loguru import logger
from sqlalchemy import Column, Integer, BigInteger, Text, String, Date, DateTime, JSON, SmallInteger, select
from sqlalchemy.ext.asyncio import AsyncSession

from .base import Base


def escape(text: str) -> str:
    escape_dict = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '{': '&#123;',
        '}': '&#125;',
        "'": '&#8242;',
        '"': '&#8243;',
        '`': '&#96;',
        '=': '&#61;',
        '/': '&#47;',
        '!': '&#33;',
        '#': '&#35;',
        '$': '&#36;',
        '%': '&#37;',
        '^': '&#94;',
        '(': '&#40;',
        ')': '&#41;',
        '+': '&#43;',
        '[': '&#91;',
        ']': '&#93;',
        '|': '&#124;',
        '?': '&#63;',
        ',': '&#44;',
        '.': '&#46;',
        ':': '&#58;',
        ';': '&#59;',
        '~': '&#126;',
        '_': '&#95;',
        '@': '&#64;',
    }
    return ''.join(escape_dict.get(char, char) for char in text)


def unescape(text: str) -> str:
    unescape_dict = {
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&#123;': '{',
        '&#125;': '}',
        '&#8242;': "'",
        '&#8243;': '"',
        '&#96;': '`',
        '&#61;': '=',
        '&#47;': '/',
        '&#33;': '!',
        '&#35;': '#',
        '&#36;': '$',
        '&#37;': '%',
        '&#94;': '^',
        '&#40;': '(',
        '&#41;': ')',
        '&#43;': '+',
        '&#91;': '[',
        '&#93;': ']',
        '&#124;': '|',
        '&#63;': '?',
        '&#44;': ',',
        '&#46;': '.',
        '&#58;': ':',
        '&#59;': ';',
        '&#126;': '~',
        '&#95;': '_',
        '&#64;': '@',
    }
    for escape_seq, char in unescape_dict.items():
        text = text.replace(escape_seq, char)
    return text


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

    @staticmethod
    async def process_user(
            session: AsyncSession,
            from_user: types.User,
            status: int = 1,
            ref: str = None,
    ) -> "User":
        request = await session.execute(
            select(User).where(User.user_id == from_user.id)
        )
        user: User = request.scalar()
        if user is None:
            user = User(
                user_id=from_user.id,
                ref=ref,
                name=escape(from_user.first_name),
                username=from_user.username,
                lang_code=from_user.language_code if from_user.language_code is not None else 'ru',
                status=status,
                reg_date=datetime.date.today(),
                death_date=None,
                last_activity=datetime.datetime.now(),
            )
            session.add(user)
            logger.info(
                'New User: {}{}'.format(user.user_id, f'\tFrom Ref: {user.ref}' if user.ref is not None else '')
            )
        else:
            user.name = escape(from_user.first_name)
            user.status = 1
            user.last_activity = datetime.datetime.now()
        user.name = unescape(user.name)
        return user


class Chat(Base):
    __tablename__ = 'chats'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, primary_key=True, unique=True)
    title = Column(Text)
    ref = Column(Text)
    status = Column(Integer)
    has_admin_rights = Column(Integer)
    reg_date = Column(Date)
    death_date = Column(Date)
    data = Column(JSON, default={})

    @staticmethod
    async def process_chat(
            session: AsyncSession,
            from_chat: types.Chat,
            status: int = 1,
            has_admin_rights: int = 0,
            ref: str = None,
    ):
        request = await session.execute(
            select(Chat).where(Chat.chat_id == from_chat.id)
        )
        chat: Chat = request.scalar()
        if chat is None:
            chat = Chat(
                chat_id=from_chat.id,
                title=escape(from_chat.title),
                ref=ref,
                status=status,
                has_admin_rights=has_admin_rights,
                reg_date=datetime.date.today(),
                death_date=None,
                data={}
            )
            session.add(chat)
            logger.info(
                'New Chat: {}{}'.format(chat.chat_id, f'\tFrom Ref: {chat.ref}' if chat.ref is not None else '')
            )
        else:
            chat.title = escape(from_chat.title)
            chat.status = status
            chat.has_admin_rights = has_admin_rights
        chat.title = unescape(chat.title)
        return chat


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
