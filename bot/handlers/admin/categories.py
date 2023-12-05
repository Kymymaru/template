from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from bot.database import Category, SubCategory, Character
from bot.keyboards.admin import reply, inline
from bot.keyboards.admin.factory import CategoriesCallback, PaginationCallback, SubCategoriesCallback
from bot.states import CategoryState, SubCategoryState
from bot.texts.admin import categories as text
from bot.utils import funcs

router = Router(name='categories')


@router.message(F.text == 'Отмена ❌')
@router.message(F.text == 'Категории')
async def categories_button(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        text=text.main,
        reply_markup=reply.categories_menu()
    )


@router.message(F.text == 'Создать категорию ➕')
async def create_category_button(message: types.Message, state: FSMContext):
    await state.set_state(CategoryState.get_category_name)
    await message.answer(
        text=text.type_category_name,
        reply_markup=reply.cancel()
    )


@router.message(CategoryState.get_category_name)
async def get_category_name(message: types.Message, state: FSMContext, session: AsyncSession):
    category = funcs.escape(message.text)
    await session.merge(
        Category(
            category=category
        )
    )
    await session.commit()
    await message.answer(
        text=text.category_successful_created,
        reply_markup=reply.categories_menu()
    )
    await state.clear()


@router.message(F.text == 'Создать подкатегорию ➕')
async def create_category_button(message: types.Message, state: FSMContext):
    await state.set_state(SubCategoryState.get_subcategory_name)
    await message.answer(
        text=text.type_subcategory_name,
        reply_markup=reply.cancel()
    )


@router.message(SubCategoryState.get_subcategory_name)
async def get_category_name(message: types.Message, state: FSMContext, session: AsyncSession):
    subcategory = funcs.escape(message.text)
    categories = (await session.execute(
        select(Category)
    )).scalars().all()
    if len(categories) == 0:
        await state.clear()
        return await message.answer(
            text=text.choose_category_id_error,
            reply_markup=reply.categories_menu()
        )
    await state.update_data(subcategory=subcategory)
    await state.set_state(SubCategoryState.get_category_id)
    await message.answer(
        text=text.choose_category_id,
        reply_markup=inline.choose_categories_for_create_subcategory(categories, page=1)
    )


@router.callback_query(SubCategoryState.get_category_id)
async def choose_category_id(call: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    data = await state.get_data()
    await session.merge(
        SubCategory(
            category_id=call.data,
            subcategory=data['subcategory']
        )
    )
    await session.commit()
    await call.message.delete()
    await call.message.answer(
        text=text.subcategory_successful_created,
        reply_markup=reply.categories_menu()
    )
    await state.clear()


@router.message(F.text == 'Список категорий 📖')
async def categories_list(message: types.Message, session: AsyncSession, page: int = 1, edit: bool = False):
    categories = (await session.execute(
        select(Category)
    )).scalars().all()
    method = message.edit_text if edit else message.answer
    if len(categories) == 0:
        return await method(
            text=text.categories_list_empty,
            reply_markup=reply.categories_menu()
        )
    await method(
        text=text.categories_list,
        reply_markup=inline.categories_list(categories, page)
    )


@router.callback_query(CategoriesCallback.filter())
async def categories_callbacks(call: types.CallbackQuery, callback_data: CategoriesCallback, session: AsyncSession):
    if callback_data.action == 'info':
        category: Category = (await session.execute(
            select(Category).where(Category.id == callback_data.id)
        )).scalar()
        subcategories = (await session.execute(
            select(SubCategory).where(SubCategory.category_id == callback_data.id)
        )).scalars().all()
        # characters_count = (await session.execute(
        #     select(func.count()).select_from(Character).where(Character.)
        # ))
        await call.message.edit_text(
            text=text.category.format(
                category.id,
                category.category,
                ', '.join([i.subcategory for i in subcategories]) if len(subcategories) != 0 else 'Ни одной',
                0  # Поменять значение на полученное из базы данных
            ),
            reply_markup=inline.category_and_subcategory_settings(
                callback_data, data_for_back='admin_categories_list'
            )
        )
    elif callback_data.action == 'del':
        category: Category = (await session.execute(
            select(Category).where(Category.id == callback_data.id)
        )).scalar()
        subcategories_count = (await session.execute(
            select(func.count()).select_from(SubCategory).where(SubCategory.category_id == callback_data.id)
        )).scalars().all()
        await call.message.edit_text(
            text=text.confirm_deleting_category.format(
                category.category,
                subcategories_count
            ),
            reply_markup=inline.confirm_deleting(
                callback_data,
                PaginationCallback(
                    info='admin_categories_list',
                    page=callback_data.page
                ).pack()
            )
        )
    elif callback_data.action == 'delete':
        await session.execute(
            delete(Category).where(Category.id == callback_data.id)
        )
        await session.commit()
        await categories_list(call.message, session, callback_data.page)


@router.message(F.text == 'Список подкатегорий 📖')
async def subcategories_list(message: types.Message, session: AsyncSession, page: int = 1, edit: bool = False):
    subcategories = (await session.execute(
        select(SubCategory)
    )).scalars().all()
    method = message.edit_text if edit else message.answer
    if len(subcategories) == 0:
        return await method(
            text=text.subcategories_list_empty,
            reply_markup=reply.categories_menu()
        )
    await method(
        text=text.subcategories_list,
        reply_markup=inline.subcategories_list(subcategories, page)
    )


@router.callback_query(SubCategoriesCallback.filter())
async def categories_callbacks(call: types.CallbackQuery, callback_data: SubCategoriesCallback, session: AsyncSession):
    if callback_data.action == 'info':
        subcategory: SubCategory = (await session.execute(
            select(SubCategory).where(SubCategory.id == callback_data.id)
        )).scalar()
        category = (await session.execute(
            select(Category).where(Category.id == subcategory.category_id)
        )).scalar()
        # characters_count = (await session.execute(
        #     select(func.count()).select_from(Character).where(Character.su)
        # ))
        await call.message.edit_text(
            text=text.subcategory.format(
                subcategory.id,
                category.category,
                subcategory.subcategory,
                0  # тоже заменить на значение из базы данных
            ),
            reply_markup=inline.category_and_subcategory_settings(
                callback_data, data_for_back='admin_subcategories_list'
            )
        )
    elif callback_data.action == 'del':
        subcategory: SubCategory = (await session.execute(
            select(SubCategory).where(SubCategory.id == callback_data.id)
        )).scalar()
        await call.message.edit_text(
            text=text.confirm_deleting_subcategory.format(
                subcategory.subcategory
            ),
            reply_markup=inline.confirm_deleting(
                callback_data,
                PaginationCallback(
                    info='admin_subcategories_list',
                    page=callback_data.page
                ).pack()
            )
        )
    elif callback_data.action == 'delete':
        await session.execute(
            delete(SubCategory).where(SubCategory.id == callback_data.id)
        )
        await session.commit()
        await subcategories_list(call.message, session, callback_data.page)
