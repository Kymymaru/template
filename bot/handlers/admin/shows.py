from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import Show
from bot.keyboards.admin.factory import ShowsCallback
from bot.states import ShowsState
from bot.utils.shows import send_show
from bot.keyboards.admin import inline, reply
from bot.texts.admin import shows as text

router = Router(name='shows')


@router.message(F.text == 'Показы 👀')
async def main(message: types.Message, state: FSMContext, session: AsyncSession, page: int = 1, edit: bool = False):
    shows = (await session.execute(select(Show))).scalars().all()
    keyboard = inline.show_markups(shows, page)
    method = message.edit_text if edit else message.answer
    await method(
        text=text.main,
        reply_markup=keyboard
    )
    await state.clear()


@router.callback_query(ShowsCallback.filter())
async def shows_callbacks(call: types.CallbackQuery, callback_data: ShowsCallback, state: FSMContext,
                          session: AsyncSession, config):
    data = callback_data
    if data.action == 'close':
        await state.clear()
        return await call.message.delete()
    if data.action == 'add':
        await state.set_state(ShowsState.get_post)
        message_id = (await call.message.edit_text(
            text.get_post,
            reply_markup=inline.cancel
        )).message_id
        await state.update_data(message_id=message_id)
    elif data.action == 'info':
        show = await session.get(Show, data.id)
        await send_show(session, call, show, config.bot.username, check=False)
        await call.answer()
    elif data.action == 'status':
        data.status = int(not data.status)
        info = f'Показ {data.numerate_id} выключен ❎'
        if bool(data.status):
            info = f'Показ {data.numerate_id} включен ✅'
        await session.execute(update(Show).where(Show.id == data.id).values(status=data.status))
        await session.commit()
        await call.answer(info)
        await main(call.message, state, session, page=data.page, edit=True)
    elif data.action == 'progress':
        show: Show = await session.get(Show, data.id)
        await call.answer(
            text.progress.format(data.numerate_id, show.sent, show.need_to_sent),
            show_alert=True
        )
    elif data.action == 'del':
        await call.message.edit_text(
            text.confirm_delete.format(data.numerate_id),
            reply_markup=inline.confirm_deleting(data)
        )
    elif data.action == 'delete':
        await session.execute(delete(Show).where(Show.id == data.id))
        await session.commit()
        await call.answer(text.delete.format(data.numerate_id))
        await main(call.message, state, session, page=data.page, edit=True)


@router.callback_query(F.data == 'cancel', ShowsState.get_sent_count)
@router.callback_query(F.data == 'cancel', ShowsState.get_post)
async def canceling_on_get_post_state(call: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    await main(call.message, state, session, edit=True)


@router.message(ShowsState.get_post)
async def get_post_state(message: types.Message, state: FSMContext):
    message_id = (await state.get_data()).get('message_id')
    await message.bot.delete_message(
        message.from_user.id,
        message_id=message_id
    )
    await message.delete()
    html_text = message.html_text
    if message.content_type == 'text':
        file_id = None
        file_type = 'text'
    elif message.photo:
        file_id = message.photo[-1].file_id
        file_type = 'photo'
    elif message.video:
        file_id = message.video.file_id
        file_type = 'video'
    elif message.voice:
        file_id = message.voice.file_id
        file_type = 'voice'
    elif message.animation:
        file_id = message.animation.file_id
        file_type = 'animation'
    elif message.video_note:
        file_id = message.video_note.file_id
        file_type = 'video_note'
    else:
        file_id = message.document.file_id
        file_type = 'document'
    keyboard = {'inline_keyboard': []} if message.reply_markup else None
    if keyboard is not None:
        for row in message.reply_markup.inline_keyboard:
            rows = []
            for button in row:
                rows.append(
                    {'text': button.text,
                     'url': button.url}
                )
            keyboard['inline_keyboard'].append(rows)

    await state.set_data({
        'text': html_text,
        'file_type': file_type,
        'file_id': file_id,
        'keyboard': keyboard
    })
    await state.set_state(ShowsState.get_sent_count)
    await message.answer(
        text.get_sent_count,
        reply_markup=inline.cancel
    )


@router.message(ShowsState.get_sent_count)
async def get_sent_count_state(message: types.Message, state: FSMContext, session: AsyncSession):
    need_sent = message.text
    if need_sent.isdigit():
        need_sent = int(need_sent)
        if need_sent < 0:
            return await message.answer('<b>Введите число больше 0</>')
        data = await state.get_data()
        await session.merge(
            Show(
                text=data['text'],
                file_id=data['file_id'],
                file_type=data['file_type'],
                keyboard=data['keyboard'],
                need_to_sent=need_sent
            )
        )
        await session.commit()
        await message.answer(text.success_add, reply_markup=reply.main_admin())
        await main(message, state, session)
    else:
        await message.answer('<b>Введите число!</>')
