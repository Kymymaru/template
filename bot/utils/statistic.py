import datetime as dt

from sqlalchemy import select, func

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import User, Bill, Chat
from bot.keyboards.admin.factory import ReferralCallback


class StatParam:
    days = 20
    width = 10


def splitting(number):
    if number == 0:
        return ""
    return str(round(number / 1000, 1)) + 'k'


async def audit_stat(session: AsyncSession) -> str:
    today = dt.datetime.today()
    day = dt.timedelta(days=1)
    offset1 = today.strftime('%Y-%m-%d %H:%M:%S')
    offset2 = (today - day).strftime('%Y-%m-%d %H:%M:%S')
    count_active = []
    count_not = []
    count_not_ref = []
    for _ in range(StatParam.days):
        statement = select(func.count()).select_from(User)
        count = (await session.execute(statement.where(User.reg_date > offset2, User.reg_date < offset1))).scalar()
        count2 = (await session.execute(
            statement.where(User.status == 0, User.reg_date > offset2, User.reg_date < offset1))).scalar()
        count3 = (await session.execute(
            statement.where(User.reg_date > offset2, User.reg_date < offset1, User.ref.is_(None)))).scalar()

        count_active.append(count)
        count_not.append(count2)
        count_not_ref.append(count3)

        offset1 = offset2
        offset2 = (dt.datetime.strptime(offset2, '%Y-%m-%d %H:%M:%S') - day).strftime('%Y-%m-%d %H:%M:%S')

    data = count_active[::-1]
    data2 = count_not[::-1]
    data3 = count_not_ref[::-1]
    color1 = '#645fd5'
    color2 = '#ae1311'
    color3 = '#00FF00'

    fig, ax = plt.subplots(figsize=(StatParam.width, 6), facecolor='white', dpi=100)
    max_value = max(data)
    ax.set_ylim((-max_value / 100 * 5, max_value + max_value / 100 * 10))  # type: ignore

    ax.set_title(f'Статистика за последние {len(data)} дней', fontdict={'size': 18})
    ax.set(ylabel='Не закинул на чай кодеру ? аудита не будет!')
    dts_result = ['Сегодня', 'Вчера']
    datetime = today - day * 2
    for _ in range(len(data) - 2):
        dts_result.append(datetime.strftime('%d.%m'))
        datetime -= day

    plt.xticks(range(len(data3)), dts_result[::-1], rotation=60, horizontalalignment='center', fontsize=10)

    offset = -0.1
    ax.bar([i + offset for i in range(len(data3))], data3, color=color3, width=0.2, alpha=1)

    for i, cty in enumerate(data3):
        ax.text(i + offset, -(max_value / 100 * 3), splitting(cty), horizontalalignment='center', color=color3,
                fontsize=8, alpha=0.8)

    offset = -0.4
    ax.bar([i + offset for i in range(len(data))], data, color=color1, width=0.2, alpha=1)

    for i, cty in enumerate(data):
        ax.text(i + offset, cty + (max_value / 100 * 2), splitting(cty), horizontalalignment='center', color=color1,
                fontsize=5)

    offset = 0.2
    ax.bar([i + offset for i in range(len(data2))], data2, color=color2, width=0.2, alpha=1)

    for i, cty in enumerate(data2):
        ax.text(i + offset, cty + (max_value / 100 * 2), splitting(cty), horizontalalignment='center', color=color2,
                fontsize=5, alpha=0.8)

    ax.legend(handles=(
        mpatches.Patch(color=color1, label='Все'),
        mpatches.Patch(color=color3, label='Саморост'),
        mpatches.Patch(color=color2, label='Блок'),
    ))

    path = 'bot/tmp/audit_stat.png'
    plt.tight_layout()
    plt.savefig(path)

    return path


async def payment_stat(session: AsyncSession) -> str:
    today = dt.datetime.today()
    day = dt.timedelta(days=1)
    offset1 = today.strftime('%Y-%m-%d %H:%M:%S')
    offset2 = (today - day).strftime('%Y-%m-%d %H:%M:%S')
    money = []

    for _ in range(StatParam.days):
        amount = (await session.execute(
            select(Bill.amount).where(Bill.bill_date >= offset2, Bill.bill_date < offset1))).scalars().all()
        money.append(sum(amount))
        offset1 = offset2
        offset2 = (dt.datetime.strptime(offset2, '%Y-%m-%d %H:%M:%S') - day).strftime('%Y-%m-%d %H:%M:%S')

    data = money[::-1]
    color1 = '#645fd5'

    fig, ax = plt.subplots(figsize=(StatParam.width, 6), facecolor='white', dpi=100)
    max_value = max(data)
    ax.set_ylim((-max_value / 100 * 5, max_value + max_value / 100 * 10))  # type: ignore

    datetime = today
    dts_result = []
    for _ in range(len(data)):
        dts_result.append(datetime.strftime('%d.%m'))
        datetime -= day

    ax.set_title(f"Статистика c {dts_result[-1]} по {dts_result[0]}", fontdict={'size': 18})
    ax.set(ylabel='Поделись с кодером...')

    plt.xticks(range(len(data)), dts_result[::-1], rotation=60, horizontalalignment='center', fontsize=10)

    offset = -0.1
    ax.bar([i + offset for i in range(len(data))], data, color=color1, width=0.4, alpha=1)
    for i, cty in enumerate(data):
        ax.text(i + offset, cty + (max_value / 100 * 2), splitting(cty), horizontalalignment='center', color=color1,
                fontsize=10)

    ax.legend(handles=(
        mpatches.Patch(color=color1, label='Заработок, ₽'),
    ))
    path = 'bot/tmp/payment_stat.png'
    plt.tight_layout()
    plt.savefig(path)

    return path


async def ref_stat(session: AsyncSession, data: ReferralCallback) -> str:
    today = dt.datetime.today()
    day = dt.timedelta(days=1)
    offset1 = today.strftime('%Y-%m-%d %H:%M:%S')
    offset2 = (today - day).strftime('%Y-%m-%d %H:%M:%S')
    count_all = []
    count_live = []
    count_death = []
    for _ in range(StatParam.days):
        table = User if data.type == 'user' else Chat
        count = (await session.execute(
            select(func.count()).select_from(table).where(
                table.ref == data.ref, table.reg_date >= offset2,
                table.reg_date < offset1
            )
        )).scalar()
        count2 = (await session.execute(
            select(func.count()).select_from(table).where(
                table.ref == data.ref, table.status == 1,
                table.reg_date >= offset2,
                table.reg_date < offset1
            )
        )).scalar()
        count3 = (await session.execute(
            select(func.count()).select_from(table).where(
                table.ref == data.ref, table.status == 0,
                table.death_date >= offset2,
                table.death_date < offset1
            )
        )).scalar()
        count_all.append(count)
        count_live.append(count2)
        count_death.append(count3)

        offset1 = offset2
        offset2 = (dt.datetime.strptime(offset2, '%Y-%m-%d %H:%M:%S') - day).strftime('%Y-%m-%d %H:%M:%S')

    count_all = count_all[::-1]
    count_live = count_live[::-1]
    count_death = count_death[::-1]
    blue = '#645fd5'
    green = '#00FF00'
    red = '#ae1311'

    fig, ax = plt.subplots(figsize=(StatParam.width, 6), facecolor='white', dpi=100)
    max_value = max(count_all)
    ax.set_ylim((-max_value / 100 * 5, max_value + max_value / 100 * 10))  # type: ignore

    ax.set_title(f'Статистика реф. ссылки "{data.ref}" в {"лс" if data.type == "user" else "чатах"} за последние {len(count_all)} дней', fontdict={'size': 18})
    ax.set(ylabel='Не закинул на чай кодеру ? аудита не будет!')
    dts_result = ['Сегодня', 'Вчера']
    datetime = today - day * 2
    for _ in range(len(count_all) - 2):
        dts_result.append(datetime.strftime('%d.%m'))
        datetime -= day

    plt.xticks(range(len(count_all)), dts_result[::-1], rotation=60, horizontalalignment='center', fontsize=10)

    offset = -0.1
    ax.bar([i + offset for i in range(len(count_live))], count_live, color=green, width=0.2, alpha=1)

    for i, cty in enumerate(count_live):
        ax.text(i + offset, -(max_value / 100 * 3), splitting(cty), horizontalalignment='center', color=green,
                fontsize=8, alpha=0.8)

    offset = -0.4
    ax.bar([i + offset for i in range(len(count_all))], count_all, color=blue, width=0.2, alpha=1)

    for i, cty in enumerate(count_all):
        ax.text(i + offset, cty + (max_value / 100 * 2), splitting(cty), horizontalalignment='center', color=blue,
                fontsize=5)

    offset = 0.2
    ax.bar([i + offset for i in range(len(count_death))], count_death, color=red, width=0.2, alpha=1)

    for i, cty in enumerate(count_death):
        ax.text(i + offset, cty + (max_value / 100 * 2), splitting(cty), horizontalalignment='center', color=red,
                fontsize=5, alpha=0.8)

    ax.legend(handles=(
        mpatches.Patch(color=blue, label='Всего'),
        mpatches.Patch(color=green, label='Живые'),
        mpatches.Patch(color=red, label='Мертвые'),
    ))

    path = 'bot/tmp/ref_stat.png'
    plt.tight_layout()
    plt.savefig(path)

    return path
