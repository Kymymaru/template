import datetime
import json
from typing import Any
import requests

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import Bill


def get_percent(all_count, count):
    try:
        return round((count / all_count) * 100)
    except ZeroDivisionError:
        return 0


async def get_money(date, session: AsyncSession) -> tuple:
    request = await session.execute(
        select(Bill.amount).where(Bill.bill_date >= date[0], Bill.bill_date < date[1])
    )
    data = request.scalars().all()
    response = (
        sum(data),
        (round(sum(data) / len(data), 2) if len(data) > 0 else 0),
        len(data)
    )
    return response


def get_times() -> tuple:
    today = datetime.datetime.today()
    yesterday = (today - datetime.timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
    last_week = (today - datetime.timedelta(weeks=1)).strftime('%Y-%m-%d %H:%M:%S')
    last_month = (today - datetime.timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')

    return (yesterday, today), (last_week, today), (last_month, today)


async def get_count(session: AsyncSession, table: Any, *filt):
    r = await session.execute(select(func.count()).select_from(table).where(*filt))
    return r.scalar()


def escape(text: str) -> str:
    return (
        text
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('{', '&#123;')
        .replace('}', '&#125;')
        .replace("'", '&#8242;')
        .replace('"', '&#8243;')
    )


def splitting(number: int, offset: int = 3, symb: str = '.') -> str:
    result = ""
    number = str(number).replace(' ', "")
    for i, item in enumerate(number[::-1], start=1):
        result += item
        if i % offset == 0:
            result += ' '
    return result[::-1].strip().replace(' ', symb)


def numerate(numbers):
    data = {
        0: '0️⃣',
        1: '1️⃣',
        2: '2️⃣',
        3: '3️⃣',
        4: '4️⃣',
        5: '5️⃣',
        6: '6️⃣',
        7: '7️⃣',
        8: '8️⃣',
        9: '9️⃣',
        10: '🔟'
    }
    text = ''
    for number in str(numbers):
        text += data[int(number)]
    return text


def format_text(from_user, text: str, username: str):
    text = text.replace(
        '$first_name', f'{from_user.first_name}'
    ).replace(
        '$last_name', f'{from_user.last_name}'
    ).replace(
        '$full_name', f'{from_user.full_name}'
    ).replace(
        '$bot', f'{username}'
    ).replace(
        '$id', f'{from_user.id}'
    ).replace(
        '$username', f'{from_user.username if from_user.username else from_user.full_name}'
    )
    return text


def sec_to_time(seconds: int, maximum: str = 'days') -> dict:
    index = ('seconds', 'minutes', 'hours', 'days').index(maximum)

    days = 0
    if index >= 3:
        days = seconds // (60 * 60 * 24)
        seconds -= days * (60 * 60 * 24)

    hours = 0
    if index >= 2:
        hours = seconds // (60 * 60)
        seconds -= hours * 60 * 60

    minutes = 0
    if index >= 1:
        minutes = seconds // 60
        seconds -= minutes * 60

    return {
        'days': days,
        'hours': hours,
        'minutes': minutes,
        'seconds': int(seconds),
    }


def markup_to_json(reply_markup):
    keyboard = {'inline_keyboard': []} if reply_markup is not None else None
    if keyboard is not None:
        for row in reply_markup.inline_keyboard:
            rows = []
            for button in row:
                rows.append(
                    {
                        'text': button.text,
                        'url': button.url
                    }
                )
            keyboard['inline_keyboard'].append(rows)
    return keyboard

