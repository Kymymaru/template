import datetime
from typing import Union
import time
import asyncio

from aiogram import exceptions, Bot
from loguru import logger
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.admin import reply
from bot.utils import funcs
from bot.database import Mailing, Settings, User
from bot.texts.admin import mailing as mailing_text

MAILING = False


class MailingUtility:
    def __init__(self,
                 session: AsyncSession,
                 settings: Settings,
                 bot: Bot,
                 admin_id: int,
                 time_start: int,
                 users: list,
                 speed: int,
                 count_of_sent: int = 0,
                 result: dict = None,
                 ):
        self.session = session
        self.notification = True
        self.not_active = []
        self.admin_id = admin_id
        self.time_start = time_start
        self.bot = bot
        self.users = users
        self.speed = speed
        self.last_speed_limit = 0

        count = settings.count
        chat_id = settings.chat_id
        message_id = settings.message_id
        keyboard = settings.keyboard

        self.chat_id = chat_id
        self.message_id = message_id
        self.keyboard = keyboard

        self.count_of_sent = count_of_sent
        self.count = count

        if result is None:
            result = {'true': 0, 'not_sub': 0, 'block': 0, 'none': 0}
        self.result = result

    async def start(self):
        global MAILING
        MAILING = True

        part = 0
        tasks = []
        #  Проходимся по юзерам и выносим отправку поста
        for user_id in self.users[self.count_of_sent:]:
            self.count_of_sent += 1
            task = self._send(user_id, self.keyboard)
            tasks.append(task)
            if all((
                    len(tasks) < self.speed,
                    self.count_of_sent < len(self.users),
                    self.result['true'],
            )):
                continue

            if self.last_speed_limit and self.last_speed_limit + 5 >= time.monotonic():
                await asyncio.sleep(5)

            part += 1
            timer = time.perf_counter_ns()
            try:
                await asyncio.gather(*tasks)
            except:
                pass
            tasks.clear()

            sleep = 1 - ((time.perf_counter_ns() - timer) / 10 ** 9)
            await asyncio.sleep(sleep if sleep > 0 else 0)

            print('{}{} / {}  {}'.format(
                ' ' * (12 - len(str(user_id))),
                self.count_of_sent, len(self.users),
                self.result,
            ))

            if not MAILING:
                break

            if part >= 4:
                part = 0
                try:
                    mailing = await Mailing.get_mailing()
                    await mailing.update(MailingCount=self.count_of_sent, Result=self.result)
                except:
                    pass

            if len(self.not_active) >= 100:
                await update_active(self.session, self.not_active)
                self.not_active.clear()

            if self.count and self.result['true'] >= self.count:
                break

            mailing = (await self.session.execute(select(Mailing))).scalar()
            if self.count_of_sent % 50 == 0 and not mailing:
                break

        if self.not_active:
            await update_active(self.session, self.not_active)

        data = funcs.sec_to_time(datetime.datetime.now().timestamp() - self.time_start, maximum='hours')
        hours, minutes, seconds = data['hours'], data['minutes'], data['seconds']

        text = mailing_text.finished.format(
            self.result['true'],
            self.result['not_sub'],
            self.result['block'],
            self.result['none'],
            f'{hours}ч. {minutes}м. {seconds}с.',
        )
        try:
            await self.bot.send_message(self.admin_id, text, reply_markup=reply.main_admin())
            await self.session.execute(delete(Mailing))
            await self.session.execute(delete(Settings))
        except:
            pass

    async def _send(self, user_id: int, keyboard) -> Union[bool, None]:
        try:
            await self.bot.copy_message(user_id, self.chat_id, self.message_id, reply_markup=keyboard)
        except exceptions.TelegramBadRequest:
            self.result['none'] += 1

        except exceptions.TelegramForbiddenError:
            self.result['block'] += 1

        except exceptions.TelegramRetryAfter as e:
            drop = 1
            time_now = time.monotonic()

            if self.last_speed_limit + 5 >= time_now:
                return

            self.last_speed_limit = time_now
            print(f'Лимит: ({e.retry_after}sec)  {self.speed} = {self.speed - drop}')
            self.speed -= drop

            await asyncio.sleep(e.retry_after)

            await self.session.execute(update(Mailing).values(speed=self.speed))
            text = mailing_text.limit.format(self.speed)
            try:
                await self.bot.send_message(self.admin_id, text)
            except:
                pass
            return

        except exceptions.TelegramAPIError:
            return

        except Exception as e:
            logger.error(f'Ошибка: ({str(e)})')
            text = mailing_text.error.format(str(e))
            try:
                await self.bot.send_message(self.admin_id, text)
            except:
                pass
            return

        else:
            self.result['true'] += 1

            if self.notification:
                self.notification = False

                text = mailing_text.start
                try:
                    await self.bot.send_message(self.admin_id, text)
                except:
                    pass
            return True

        self.result['not_sub'] += 1
        self.not_active.append(user_id)
        return False


async def update_active(session: AsyncSession, not_active: list):
    division = 1000
    indexs = (0, division)
    users = not_active[indexs[0]: indexs[1]]
    while users:
        try:
            await session.execute(update(User).where(User.user_id.in_(users)).values(status=0))
        except:
            pass

        indexs = (indexs[0] + division, indexs[1] + division)
        users = not_active[indexs[0]: indexs[1]]


async def start(
        session: AsyncSession,
        settings: Settings,
        bot: Bot,
        admin_id: int,
        users: list,
        speed: int,
):
    time_start = datetime.datetime.now().timestamp()
    await session.merge(
        Mailing(
            count=settings.count,
            chat_id=settings.chat_id,
            message_id=settings.message_id,
            keyboard=settings.keyboard,
            speed=speed,
            start=time_start,
            mailing_count=0,
            mailing_limit=len(users),
            result=None
        )
    )
    mailing = MailingUtility(session, settings, bot, admin_id, time_start, users, speed, 0)
    await mailing.start()


async def stop(session: AsyncSession) -> bool:
    global MAILING

    status = MAILING

    if MAILING:
        MAILING = False

    await session.execute(delete(Mailing))
    await session.execute(delete(Settings))
    logger.info('Mailing stopping..')
    return status
