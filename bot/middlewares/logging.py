import json
import loguru
import time
from typing import Callable, Awaitable, Any, Dict, cast
from aiogram import BaseMiddleware
from aiogram.types import Update, TelegramObject


class LoggingMiddleware(BaseMiddleware):
    def __init__(self):
        self.logger = loguru.logger
        super(LoggingMiddleware, self).__init__()

    @staticmethod
    def get_time(_started_processing_at):
        return round((time.time() - _started_processing_at) * 1000)

    async def __call__(
            self,
            handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        event = cast(Update, event)
        _started_processing_at = time.time()
        if event.message:
            message = event.message
            self.logger.info(
                f"Received message [ID:{message.message_id}] in chat [{message.chat.type}:{message.chat.id}]"
            )
            try:
                await handler(event, data)
                self.logger.success(f'Handled in {self.get_time(_started_processing_at)} ms')
            except Exception as err:
                data = json.loads(event.json())
                data['error'] = err
                if message.content_type == 'text':
                    self.logger.error(f'Error during handle text: {event.message.text}\n{data}')
                else:
                    self.logger.error(f'Error during handle {message.content_type}\n{data}')
        elif event.callback_query:
            callback_query = event.callback_query
            if callback_query.message:
                message = callback_query.message
                text = (f"Received callback query [ID:{callback_query.id}] "
                        f"from user [ID:{callback_query.from_user.id}] "
                        f"for message [ID:{message.message_id}] "
                        f"in chat [{message.chat.type}:{message.chat.id}] "
                        f"with data: {callback_query.data}")

                if message.from_user:
                    text = f"{text} originally posted by user [ID:{message.from_user.id}]"

                self.logger.info(text)

            else:
                self.logger.info(f"Received callback query [ID:{callback_query.id}] "
                                 f"from user [ID:{callback_query.from_user.id}] "
                                 f"for inline message [ID:{callback_query.inline_message_id}] ")

            try:
                await handler(event, data)
                await event.callback_query.answer()
                self.logger.success(f'Handled in {self.get_time(_started_processing_at)} ms')
            except Exception as err:
                data = json.loads(event.json())
                data['error'] = err
                self.logger.error(f'Error during handle callback_data: {event.callback_query.data}\n{data}')

        elif event.my_chat_member:
            my_chat_member_update = event.my_chat_member
            self.logger.info(f"Received my chat member update "
                             f"for user [ID:{my_chat_member_update.from_user.id}]. "
                             f"Old state: {my_chat_member_update.old_chat_member.json()} "
                             f"New state: {my_chat_member_update.new_chat_member.json()} ")
            try:
                await handler(event, data)
                self.logger.success(f'Handled in {self.get_time(_started_processing_at)} ms')
            except Exception as err:
                data = json.loads(event.json())
                data['error'] = err
                self.logger.error(f'Error during handle my_chat_member_update: {my_chat_member_update.from_user.id}\n'
                                  f'{data}')

        elif event.chat_member:
            chat_member_update = event.chat_member
            self.logger.info(f"Received chat member update "
                             f"for user [ID:{chat_member_update.from_user.id}]. "
                             f"Old state: {chat_member_update.old_chat_member.json()} "
                             f"New state: {chat_member_update.new_chat_member.json()} ")
            try:
                await handler(event, data)
                self.logger.success(f'Handled in {self.get_time(_started_processing_at)} ms')
            except Exception as err:
                data = json.loads(event.json())
                data['error'] = err
                self.logger.error(f'Error during handle chat_member_update: {chat_member_update.from_user.id}\n{data}')

        elif event.chat_join_request:
            chat_join_request = event.chat_join_request
            self.logger.info(f"Received chat join request "
                             f"for user [ID:{chat_join_request.from_user.id}] "
                             f"in chat [ID:{chat_join_request.chat.id}]")
            try:
                await handler(event, data)
                self.logger.success(f'Handled in {self.get_time(_started_processing_at)} ms')
            except Exception as err:
                data = json.loads(event.json())
                data['error'] = err
                self.logger.error(f'Error during handle chat_join_request: {chat_join_request.from_user.id}\n{data}')
