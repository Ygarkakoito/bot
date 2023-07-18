from datetime import datetime
import os
import logging

from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
from aiogram_timepicker.panel import FullTimePicker, full_timep_callback, full_timep_default, \
    HourTimePicker, hour_timep_callback, MinuteTimePicker, minute_timep_callback, \
    SecondTimePicker, second_timep_callback, \
    MinSecTimePicker, minsec_timep_callback, minsec_timep_default
from aiogram_timepicker import result, carousel, clock
import aiogram
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Command
from sqlalchemy.orm import sessionmaker
from states import States
from main import engine
from models import User, Activity, City
from main import dp, bot
from models import Ad
import asyncio
from typing import List
from sqlalchemy import delete, desc, create_engine
from bot import dp, start, search_movies, search_movies, select_cinema, process_simple_calendar, page, cancel_handler, \
    show_main_menu, session
from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import calendar
import locale
locale.setlocale(locale.LC_TIME, 'ru_RU')
from PIL import Image
import os


from aiogram.types import CallbackQuery
from aiogram_calendar import SimpleCalendar, simple_cal_callback
from datetime import date as d
simple_calendar = SimpleCalendar()


Session = sessionmaker(bind=engine)


@dp.message_handler(commands=['change_location'], state='*')
async def cmd_edit_profile(message: types.Message, state: FSMContext):
    session = Session()
    cities = session.query(City).all()
    keyboard = types.InlineKeyboardMarkup()
    if cities:
        for city in cities:
            keyboard.add(types.InlineKeyboardButton(city.name, callback_data=f'edit_city_{city.id}'))
    await message.answer('Выберите город:', reply_markup=keyboard)
    session.close()
@dp.message_handler(commands=['edit_profile'], state='*')
async def cmd_edit_profile(message: types.Message):
    global save_counter  # Объявляем глобальную переменную
    save_counter = 0
    print(save_counter)
    user_id = message.from_user.id
    session = Session()
    user = session.query(User).filter(User.id == user_id).first()
    session.close()
    if user:
        await send_profile_and_buttons(message, user)
        await message.delete()


async def send_profile_and_buttons(message: types.Message, user: User):
    global save_counter  # Объявляем глобальную переменную
    save_counter = 0
    print(save_counter)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton('⚠️ Имя', callback_data='edit_name'),
        types.InlineKeyboardButton('📸 Фото', callback_data='edit_photo'),
    )

    session = Session()  # Создаем сеанс базы данных
    city_name = session.query(City).filter_by(id=user.city_id).first()
    session.close()  # Закрываем сеанс базы данных
    keyboard.add(types.InlineKeyboardButton('🌍 Город', callback_data='edit_city'),
                 types.InlineKeyboardButton('📱 Телефон', callback_data='edit_contact'),)
    result = "Информация о профиле:\n"
    result += f"Имя: {user.name}\n"
    result += f"Telegram ID: {user.id}  Username: @{user.username}\n"
    result += f"Контактные данные: {user.contact}\n"
    result += f"Город: {city_name.name if city_name else None}\n"
    if user.photo_id:
        await message.answer_photo(photo=user.photo_id, caption=result, reply_markup=keyboard)
    else:
        await message.answer(result, reply_markup=keyboard)



@dp.callback_query_handler(lambda c: c.data == 'back_to_edit_profile', state='*')
async def callback_back_to_edit_profile(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await cmd_edit_profile(callback_query.message)
    await callback_query.message.delete()


@dp.callback_query_handler(lambda c: c.data in ['edit_name','edit_contact_city', 'edit_photo', 'view_results', 'back_to_edit_profile'], state='*')
async def process_edit_profile_action(callback_query: types.CallbackQuery, state: FSMContext):
    action = callback_query.data
    await callback_query.answer()
    if action == 'edit_name':
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_edit_profile'))
        await callback_query.message.answer('Отправьте новое имя профиля:', reply_markup=keyboard)
        await States.edit_name.set()
    elif action == 'edit_photo':
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_edit_profile'))
        await callback_query.message.answer('Отправьте новое фото профиля:', reply_markup=keyboard)
        await States.edit_photo.set()
    elif action == 'edit_contact':
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton('📱 номер телефона', callback_data='edit_contact'),
        )
    elif action == 'edit_city':
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton('🌍 город', callback_data='edit_city'),
        )
        await callback_query.message.answer('Выберите опцию для обновления контактных данных:', reply_markup=keyboard)
        await States.edit_contact.set()


@dp.callback_query_handler(lambda c: c.data.startswith('edit_city_'), state='*')
async def process_edit_city(callback_query: types.CallbackQuery, state: FSMContext):
    city_id = int(callback_query.data.split('_')[2])
    await state.update_data(city_id=city_id)
    data = await state.get_data()
    user_id = callback_query.from_user.id
    session = Session()
    user = session.query(User).filter(User.id == user_id).first()
    user.city_id = data.get('city_id')
    session.commit()
    session.close()
    await callback_query.message.answer('Город успешно обновлен!')
    await state.finish()
    try:
        await callback_query.message.delete()
    except aiogram.utils.exceptions.MessageToDeleteNotFound:
        pass
    try:
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id - 1)
    except aiogram.utils.exceptions.MessageToDeleteNotFound:
        pass
    try:
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id + 1)
    except aiogram.utils.exceptions.MessageToDeleteNotFound:
        pass
    try:
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id - 2)
    except aiogram.utils.exceptions.MessageToDeleteNotFound:
        pass
    try:
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id - 3)
    except aiogram.utils.exceptions.MessageToDeleteNotFound:
        pass
    session = Session()
    user = session.query(User).filter(User.id == user_id).first()
    session.close()
    await send_profile_and_buttons(callback_query.message, user)


@dp.message_handler(state=States.edit_contact)
async def process_edit_contact_number(message: types.Message, state: FSMContext):
    contact = message.text.strip()
    if contact:
        await state.update_data(contact=contact)
        data = await state.get_data()
        user_id = message.from_user.id
        session = Session()
        user = session.query(User).filter(User.id == user_id).first()
        user.contact = data.get('contact')
        session.commit()
        session.close()
        await message.answer('Контактные данные успешно обновлены!')
        await state.finish()
        await cmd_edit_profile(message)
        if message.reply_to_message:
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=message.reply_to_message.message_id)
            except aiogram.utils.exceptions.MessageToDeleteNotFound:
                pass
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
        except aiogram.utils.exceptions.MessageToDeleteNotFound:
            pass
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id + 1)
        except aiogram.utils.exceptions.MessageToDeleteNotFound:
            pass
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 3)
        except aiogram.utils.exceptions.MessageToDeleteNotFound:
            pass
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 4)
        except aiogram.utils.exceptions.MessageToDeleteNotFound:
            pass
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 2)
        except aiogram.utils.exceptions.MessageToDeleteNotFound:
            pass


@dp.callback_query_handler(lambda c: c.data == 'edit_contact', state='*')
async def process_edit_contact_button(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.answer('Введите новый контактный номер телефона:')
    await States.edit_contact.set()
    await state.update_data(callback_message_id=callback_query.message.message_id)


@dp.callback_query_handler(lambda c: c.data == 'edit_city', state='*')
async def process_edit_city_button(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    session = Session()
    cities = session.query(City).all()
    keyboard = types.InlineKeyboardMarkup()
    if cities:
        for city in cities:
            keyboard.add(types.InlineKeyboardButton(city.name, callback_data=f'edit_city_{city.id}'))
    await callback_query.message.answer('Выберите город:', reply_markup=keyboard)
    session.close()


@dp.message_handler(state=States.edit_name)
async def process_edit_name(message: types.Message, state: FSMContext):
    name = message.text.strip()
    if name:
        await state.update_data(name=name)
        data = await state.get_data()
        user_id = message.from_user.id
        session = Session()
        user = session.query(User).filter(User.id == user_id).first()
        user.name = data.get('name')
        session.commit()
        session.close()
        await message.answer('Имя успешно обновлено!')
        await state.finish()
        await cmd_edit_profile(message)
        if message.reply_to_message:
            try:
                await bot.delete_message(chat_id=message.chat.id, message_id=message.reply_to_message.message_id)
            except aiogram.utils.exceptions.MessageToDeleteNotFound:
                pass
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
        except aiogram.utils.exceptions.MessageToDeleteNotFound:
            pass
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id + 1)
        except aiogram.utils.exceptions.MessageToDeleteNotFound:
            pass
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        except aiogram.utils.exceptions.MessageToDeleteNotFound:
            pass
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id-3)
        except aiogram.utils.exceptions.MessageToDeleteNotFound:
            pass
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 4)
        except aiogram.utils.exceptions.MessageToDeleteNotFound:
            pass

        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id-2)
        except aiogram.utils.exceptions.MessageToDeleteNotFound:
            pass


@dp.message_handler(content_types=types.ContentTypes.PHOTO, state=States.create_ad_photo)
async def process_edit_photo(message: types.Message, state: FSMContext):
    global save_counter  # Объявляем глобальную переменную
    photo = message.photo[-1]
    print(message.photo)

    picture_name = f'{photo.file_id}.jpg'
    destination = os.path.join('./static', picture_name)
    photo_file = await bot.download_file_by_id(message.photo[-1].file_id, destination)

    image = Image.open(f'static/{picture_name}')
    new_image = image.resize((190, 280))
    new_image.save(f'static/{picture_name}', quality=95)


    photo_url = photo.file_id
    await state.update_data(photo_url=picture_name)
    async with state.proxy() as data:
        title = data.get('title')
        description = data.get('description')
        date = data.get('date')
        cost = data.get('cost')
        location = data.get('location')
        ad = Ad(title=title, photo_url=photo_url, description=description, date=date, cost=cost, location=location)
        session = Session()
        session.add(ad)
        session.commit()
    success_message = await message.answer('Фото объявления успешно обновлено!')
    save_counter += 1  # Увеличиваем счетчик при сохранении параметров
    print(save_counter)
    await asyncio.sleep(1)
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await bot.delete_message(chat_id=success_message.chat.id, message_id=success_message.message_id)
    except aiogram.utils.exceptions.MessageToDeleteNotFound:
        pass
    for i in range(1, 4):
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - i)
        except aiogram.utils.exceptions.MessageToDeleteNotFound:
            pass
    await send_main_menu_for_new_ad(message, state, updated_title=title)
    await States.create_ad.set()


@dp.message_handler(commands=['view_ads'])
async def view_ads(message: types.Message, state: FSMContext):
    session = Session()
    ads = session.query(Ad).all()
    session.close()
    if ads:
        current_ad_index = 0
        await send_ad(message.chat.id, ads, current_ad_index, state)
    else:
        await message.answer("Нет доступных объявлений.")


# Обработчики для навигации по объявлениям
@dp.callback_query_handler(lambda c: c.data.startswith(('next_ad_', 'prev_ad_')))
async def navigate_ads(callback_query: types.CallbackQuery, state: FSMContext):
    query_data = callback_query.data
    current_index = int(query_data.split('_')[-1])

    session = Session()
    ads = session.query(Ad).all()
    session.close()

    if query_data.startswith('next_ad_'):
        next_index = (current_index + 1) % len(ads)
    elif query_data.startswith('prev_ad_'):
        next_index = (current_index - 1) % len(ads)

    await delete_previous_message(callback_query, state)  # Delete the previous message
    await send_ad(callback_query.message.chat.id, ads, next_index, state)


async def delete_previous_message(callback_query: types.CallbackQuery, state: FSMContext):
    previous_message_id = await state.get_data()
    if previous_message_id:
        previous_message_id = previous_message_id.get('previous_message_id')
        if previous_message_id:
            await bot.delete_message(callback_query.message.chat.id, previous_message_id)


async def send_ad(chat_id: int, ads: List[Ad], index: int, state: FSMContext):
    session = Session()
    ad = ads[index]
    user = session.query(User).filter_by(id=ad.user_id).first()
    session.close()

    ad_message = f"<b>ID объявления:</b> {ad.id}\n" \
                 f"<b>Username:</b> @{user.username}\n" \
                 f"<b>Контактные данные:</b> {user.contact}\n" \
                 f"<b>Название:</b> {ad.title}\n" \
                f"<b>Описание:</b> {ad.description}\n" \
                f"<b>Дата начала:</b> {ad.date}\n" \
                 f"<b>Цена:</b> {(ad.cost)}₽\n" \
                 f"<b>Локация:</b> {ad.location}\n" \
                f"<b>Категория:</b> {ad.category}\n"

    buttons = [
        types.InlineKeyboardButton("⬅️", callback_data=f"prev_ad_{index}"),
        types.InlineKeyboardButton(f"{index + 1}/{len(ads)}", callback_data='ad_index'),
        types.InlineKeyboardButton("➡️", callback_data=f"next_ad_{index}")
    ]

    if ad.photo_url:
        message = await bot.send_photo(chat_id, photo=open(f'static/{ad.photo_url}', 'rb'), caption=ad_message,
                                       parse_mode="HTML",
                                       reply_markup=types.InlineKeyboardMarkup().row(*buttons))
    else:
        message = await bot.send_message(chat_id, ad_message, parse_mode="HTML",
                                         reply_markup=types.InlineKeyboardMarkup().row(*buttons))

    await state.update_data(previous_message_id=message.message_id)

save_counter = 0
@dp.message_handler(commands=['add_ad'], state='*')
async def handle_add_ad(message: types.Message, state: FSMContext):
    global save_counter
    save_counter = 0
    data = await state.get_data()
    required_fields = ['title', 'photo_url', 'description', 'date', 'cost', 'location']
    if all(field in data for field in required_fields):
        await message.answer('Вы нажали команду "Добавить объявление"')
        await send_main_menu_for_new_ad(message, state)
        await States.create_ad.set()
    else:
        await message.answer('Вы нажали команду "Добавить объявление"')
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton('Мероприятия', callback_data='category_1'),
            types.InlineKeyboardButton('Другое', callback_data='category_3'),
        )
        keyboard.add(types.InlineKeyboardButton('🔙 Назад', callback_data='back_to_main_menu'))
        await message.answer('Выберите категорию:', reply_markup=keyboard)
        await States.create_ad.set()
        # Удаление предыдущих сообщений
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 1)
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - 2)
        # ...


@dp.callback_query_handler(lambda c: c.data.startswith('category_'), state='*')
async def process_category_selection(callback_query: types.CallbackQuery, state: FSMContext):
    global save_counter
    save_counter += 1  # Увеличиваем счетчик при сохранении параметров
    print(save_counter)
    category = callback_query.data
    category_label = None
    if category == 'category_1':
        category_label = 'Мероприятия'
    elif category == 'category_3':
        category_label = 'Другое'
    await callback_query.answer(f'Вы выбрали категорию: {category_label}')
    user_id = callback_query.from_user.id
    await state.update_data(category=category_label, user_id=user_id)
    ad = Ad(user_id=user_id, category=category_label)
    session = Session()
    session.add(ad)
    session.commit()
    session.close()
    await States.create_ad.set()
    await send_main_menu_for_new_ad(callback_query.message, state)
    # Удаление предыдущих сообщений
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id - 1)



async def send_main_menu_for_new_ad(message: types.Message, state: FSMContext, updated_title=None, updated_photo=None,
                                    updated_description=None, updated_date=None, updated_cost=None,
                                    updated_location=None):

    async with state.proxy() as data:
        title = updated_title or data.get('title')
        photo_url = updated_photo or data.get('photo_url')
        description = updated_description or data.get('description')
        date = updated_date or data.get('date')
        cost = updated_cost or data.get('cost')
        location = updated_location or data.get('create_ad_location')
        category_label = data.get('category')
        user_id = data.get('user_id')
        contact= data.get('contact')
        username= data.get('username')
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton('Название', callback_data='create_ad_title'),
            types.InlineKeyboardButton('Фото объявления', callback_data='create_ad_photo'),
            types.InlineKeyboardButton('Описание', callback_data='create_ad_description'),
            types.InlineKeyboardButton('Дата начала', callback_data='create_ad_date'),
            types.InlineKeyboardButton('Стоимость', callback_data='create_ad_cost'),
            types.InlineKeyboardButton('Локация', callback_data='create_ad_location'),
        )
        if title and photo_url and description and date and cost and location:
            keyboard.add(
                types.InlineKeyboardButton('Опубликовать ', callback_data='add_adf'),
            )
    session = Session()
    location1 = session.query(City).filter_by(id=location).first()
    caption = 'Обновленная информация объявления:\n'
    user = session.query(User).filter(User.id == user_id).first()
    if title:
        caption += f'Название : {title}\n'
    if description:
        caption += f'Описание : {description}\n'
    if date: # Форматирование даты
        caption += f'Дата начала: {date}\n'
    if cost:  # Преобразование стоимости в целое число
        caption += f'Стоимость: {cost}₽\n'
    if category_label:
        caption += f'Категория: {category_label}\n'
    if user_id:
        caption += f'User ID: {user_id} Username: @{user.username}\n'
    if location1:
        caption += f'Локация : {location1.name} Телефон: {user.contact}\n\n'
    if photo_url:
        await message.answer_photo(photo=open(f'static/{photo_url}', 'rb'), caption=caption, reply_markup=keyboard)
    else:
        await message.answer(caption, reply_markup=keyboard)

@dp.message_handler(state=States.create_ad_title)
async def process_edit_title(message: types.Message, state: FSMContext):
    global save_counter  # Объявляем глобальную переменную
    title = message.text.strip()
    await state.update_data(title=title)
    async with state.proxy() as data:
        photo_url = data.get('photo_url')
        description = data.get('description')
        date = data.get('date')
        cost = data.get('cost')
        location = data.get('location')
        ad = Ad(title=title, photo_url=photo_url, description=description, date=date, cost=cost, location=location)
        session = Session()
        session.add(ad)
        session.commit()
    success_message = await message.answer('Название объявления успешно обновлено!')
    save_counter += 1  # Увеличиваем счетчик при сохранении параметров

    print(save_counter)
    await asyncio.sleep(1)
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await bot.delete_message(chat_id=success_message.chat.id, message_id=success_message.message_id)
    except aiogram.utils.exceptions.MessageToDeleteNotFound:
        pass
    for i in range(1, 5):
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - i)
        except aiogram.utils.exceptions.MessageToDeleteNotFound:
            pass
    await send_main_menu_for_new_ad(message, state, updated_title=title)
    await States.create_ad.set()


@dp.callback_query_handler(lambda c: c.data == 'add_adf', state='*')
async def handle_add_adf(callback_query: types.CallbackQuery, state: FSMContext):
    global save_counter
    await callback_query.answer()
    data = await state.get_data()
    title = data.get('title')
    photo_url = data.get('photo_url')
    description = data.get('description')
    date = data.get('date')
    cost = data.get('cost')
    location = data.get('create_ad_location')
    category = data.get('category')
    user_id = data.get('user_id')

    session = Session()
    location1 = session.query(City).filter_by(id=location).first()
    ad = Ad(
        user_id=user_id,
        title=title,
        photo_url=photo_url,
        description=description,
        date=date,
        cost=cost,
        location=location1.name,
        category=category
    )
    session.add(ad)
    session.commit()
    last_ad = session.query(Ad).order_by(desc(Ad.id)).first()
    last_ad_id = last_ad.id if last_ad else None

    # Update the ad object with the category and ID
    ad.category_label = category
    ad.id = last_ad_id
    # Получаем последнюю запись
    last_ad = session.query(Ad).order_by(desc(Ad.id)).first()
    # Получаем id последней записи
    last_ad_id = last_ad.id if last_ad else None
    # Проверяем, если save_counter больше 1 и есть последняя запись
    if save_counter > 1 and last_ad_id:
        # Определяем id диапазона удаляемых записей
        start_id = last_ad_id - save_counter
        end_id = last_ad_id - 1
        # Удаляем записи из базы данных в заданном диапазоне
        delete_statement = delete(Ad).where(Ad.id.between(start_id, end_id))
        session.execute(delete_statement)
        session.commit()
    save_counter_value = save_counter
    save_counter = 0
    session.close()
    await show_main_menu(callback_query.message)
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id - 1)
    await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id - 2)


@dp.callback_query_handler(lambda c: c.data == 'continue_edit', state='*')
async def handle_continue_edit(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    await callback_query.message.answer('Вы решили продолжить редактирование объявления.')
    message = callback_query.message
    session = Session()
    latest_ad = session.query(Ad).order_by(desc(Ad.id)).first()
    session.close()
    if latest_ad:
        title = latest_ad.title
        photo_url = latest_ad.photo_url
        description = latest_ad.description
        date = latest_ad.date
        cost = latest_ad.cost
        location = latest_ad.location
        data = await state.get_data()
        updated_title = data.get('title')
        updated_photo = data.get('photo_url')
        updated_description = data.get('description')
        updated_date = data.get('date')
        updated_cost = data.get('cost')
        updated_location = data.get('create_ad_location')

        location1 = session.query(City).filter_by(id=updated_location).first()

        if updated_title:
            title = updated_title
        if updated_photo:
            photo_url = updated_photo
        if updated_description:
            description = updated_description
        if updated_date:
            date = updated_date
        if updated_cost:
            cost = updated_cost
        if updated_location:
            location = location1.name
        await state.update_data(previous_message=message.text)
        await send_main_menu_for_new_ad(
            message,
            state,
            updated_title=title,
            updated_photo=photo_url,
            updated_description=description,
            updated_date=date,
            updated_cost=cost,
            updated_location=location
        )
        if 'create_ad_title' in message.text:
            await process_edit_title(message, state)
        if 'create_ad_photo' in message.text:
            await process_edit_title(message, state)
        if 'create_ad_description' in message.text:
            await process_edit_title(message, state)
        if 'create_ad_date' in message.text:
            await process_edit_title(message, state)
        if 'create_ad_cost' in message.text:
            await process_edit_title(message, state)
        if 'create_ad_location' in message.text:
            await process_edit_title(message, state)
    else:
        await message.answer('Нет предыдущей информации объявления.')


@dp.message_handler(content_types=types.ContentTypes.PHOTO, state=States.create_ad_photo)
async def process_edit_photo(message: types.Message, state: FSMContext):
    global save_counter  # Объявляем глобальную переменную
    photo = message.photo[-1]

    photo_url = photo.file_id  # Получаем идентификатор файла фотографии

    await state.update_data(photo_url=photo_url)

    async with state.proxy() as data:
        title = data.get('title')
        description = data.get('description')
        date = data.get('date')
        cost = data.get('cost')
        location = data.get('location')

        ad = Ad(title=title, photo_url=photo_url, description=description, date=date, cost=cost, location=location)
        session = Session()
        session.add(ad)
        session.commit()

    success_message = await message.answer('Фото объявления успешно обновлено!')
    save_counter += 1  # Увеличиваем счетчик при сохранении параметров

    print(save_counter)

    await asyncio.sleep(1)

    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await bot.delete_message(chat_id=success_message.chat.id, message_id=success_message.message_id)
    except aiogram.utils.exceptions.MessageToDeleteNotFound:
        pass

    for i in range(1, 4):
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - i)
        except aiogram.utils.exceptions.MessageToDeleteNotFound:
            pass

    await send_main_menu_for_new_ad(message, state, updated_title=title)
    await States.create_ad.set()



@dp.message_handler(state=States.create_ad_description)
async def process_edit_description(message: types.Message, state: FSMContext):
    global save_counter  # Объявляем глобальную переменную
    description = message.text.strip()
    await state.update_data(description=description)
    async with state.proxy() as data:
        photo_url = data.get('photo_url')
        title = data.get('title')
        date = data.get('date')
        cost = data.get('cost')
        location = data.get('location')
        ad = Ad(title=title, photo_url=photo_url, description=description, date=date, cost=cost, location=location)
        session = Session()
        session.add(ad)
        session.commit()
    success_message = await message.answer('Описание объявления успешно обновлено!')
    save_counter += 1  # Увеличиваем счетчик при сохранении параметров
    print(save_counter)
    await asyncio.sleep(1)
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await bot.delete_message(chat_id=success_message.chat.id, message_id=success_message.message_id)
    except aiogram.utils.exceptions.MessageToDeleteNotFound:
        pass
    for i in range(1, 4):
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - i)
        except aiogram.utils.exceptions.MessageToDeleteNotFound:
            pass
    await send_main_menu_for_new_ad(message, state, updated_title=title)
    await States.create_ad.set()

@dp.message_handler(state=States.create_ad_cost)
async def process_edit_cost(message: types.Message, state: FSMContext):
    global save_counter  # Объявляем глобальную переменную
    cost = message.text.strip()
    await state.update_data(cost=cost)
    async with state.proxy() as data:
        photo_url = data.get('photo_url')
        title = data.get('title')
        description=data.get('description')
        date=data.get('date')
        location =data.get('location')
        ad = Ad(title=title, photo_url=photo_url, description=description, date=date,cost=cost,location=location)
        session = Session()
        session.add(ad)
        session.commit()
    success_message = await message.answer('Описание объявления успешно обновлено!')
    save_counter += 1  # Увеличиваем счетчик при сохранении параметров
    print(save_counter)
    await asyncio.sleep(1)
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await bot.delete_message(chat_id=success_message.chat.id, message_id=success_message.message_id)
    except aiogram.utils.exceptions.MessageToDeleteNotFound:
        pass
    for i in range(1, 4):
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - i)
        except aiogram.utils.exceptions.MessageToDeleteNotFound:
            pass
    await send_main_menu_for_new_ad(message, state, updated_title=title)
    await States.create_ad.set()


@dp.message_handler(state=States.create_ad_location)
async def process_edit_location(message: types.Message, state: FSMContext):
    global save_counter  # Объявляем глобальную переменную
    location = message.text.strip()
    await state.update_data(location=location)
    async with state.proxy() as data:
        photo_url = data.get('photo_url')
        title = data.get('title')
        description = data.get('description')
        date = data.get('date')
        cost = data.get('cost')
        ad = Ad(title=title, photo_url=photo_url, description=description, date=date,cost=cost,location=location)
        session = Session()
        session.add(ad)
        session.commit()
    success_message = await message.answer('Описание объявления успешно обновлено!')
    save_counter += 1  # Увеличиваем счетчик при сохранении параметров
    print(save_counter)
    await asyncio.sleep(1)
    try:
        await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        await bot.delete_message(chat_id=success_message.chat.id, message_id=success_message.message_id)
    except aiogram.utils.exceptions.MessageToDeleteNotFound:
        pass
    for i in range(1, 5):
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id - i)
        except aiogram.utils.exceptions.MessageToDeleteNotFound:
            pass
    await send_main_menu_for_new_ad(message, state, updated_title=title)
    await States.create_ad.set()


@dp.callback_query_handler(simple_cal_callback.filter(), state='*')
async def process_date_selection(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    global save_counter  # Объявляем глобальную переменную
    selected, date = await simple_calendar.process_selection(callback_query, callback_data)
    today = d.today()
    year1, month1, day1 = map(int, str(today).split('-'))
    year2, month2, day2 = map(int, str(str(date)[:10]).split('-'))

    td = d(year1, month1, day1)

    tm_bd = d(year2, month2, day2)
    if td >= tm_bd:
        calendar_markup = await SimpleCalendar().start_calendar()
        await callback_query.message.answer("Нельзя выбрать дату, которая в прошлом",
                                            reply_markup=calendar_markup)
    else:
        if selected:
            await callback_query.message.answer(
                "Please select a time: ",
                reply_markup=await FullTimePicker().start_picker()
            )
            print(date)
            await state.update_data(date=date)


@dp.callback_query_handler(lambda c: c.data.startswith('create_ad_'), state='*')
async def process_edit_selection(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data
    if data == 'create_ad_title':
        await callback_query.answer('Вы выбрали редактирование названия объявления')
        await States.create_ad_title.set()
        await callback_query.message.answer('Введите новое название объявления:')
    elif data == 'create_ad_photo':
        await callback_query.answer('Вы выбрали редактирование фото объявления')
        await States.create_ad_photo.set()
        await callback_query.message.answer('Отправьте новое фото объявления (ответом на это сообщение):')
    elif data == 'create_ad_description':
        await callback_query.answer('Вы выбрали редактирование описания объявления')
        await States.create_ad_description.set()
        await callback_query.message.answer('Введите новое описание объявления:')
    elif data == 'create_ad_date':
        await callback_query.answer('Вы выбрали редактирование даты объявления')
        await States.create_ad_date.set()
        calendar_markup = await simple_calendar.start_calendar()
        message = await callback_query.message.answer('Выберите дату:', reply_markup=calendar_markup)
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)
    elif data == 'create_ad_cost':
        await callback_query.answer('Вы выбрали редактирование стоимости объявления')
        await States.create_ad_cost.set()
        await callback_query.message.answer('Введите новую стоимость объявления:')
    elif data == 'create_ad_location':
        await callback_query.answer('Вы выбрали редактирование локации объявления')
        await States.create_ad_location.set()
        session = Session()
        cities = session.query(City).all()
        keyboard = types.InlineKeyboardMarkup()
        if cities:
            for city in cities:
                keyboard.add(types.InlineKeyboardButton(city.name, callback_data=f'city_loc_{city.id}'))
        success_message = await callback_query.message.answer('Выберите город:', reply_markup=keyboard)
        session.close()
        await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=callback_query.message.message_id)


@dp.callback_query_handler(lambda c: c.data.startswith('city_loc_'), state='*')
async def process_edit_selection(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    print(callback_query.data)
    await state.update_data(create_ad_location=callback_query.data.split('_')[2])
    await send_main_menu_for_new_ad(callback_query.message, state)


@dp.message_handler(commands=['my_ads'], state='*')
async def view_my_ads(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    session = Session()
    ads = session.query(Ad).filter_by(user_id=user_id).all()
    session.close()

    if ads:
        current_ad_index = 0
        await send_my_ad(message.chat.id, ads, current_ad_index, state)
    else:
        await message.answer("У вас нет объявлений.")

@dp.callback_query_handler(lambda c: c.data.startswith(('next_my_ad_', 'prev_my_ad_')))
async def handle_change_my_ad(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data.split('_')
    action = data[0]
    index = int(data[1])
    await bot.answer_callback_query(callback_query.id)

    if action == 'next_my_ad_':
        await next_my_ad(callback_query.message, state, index)
    elif action == 'prev_my_ad_':
        await prev_my_ad(callback_query.message, state, index)


async def next_my_ad(message: types.Message, state: FSMContext, index: int):
    async with state.proxy() as data:
        ads = data.get('ads')
        if ads:
            index += 1
            if index >= len(ads):
                index = 0
            await send_my_ad(message.chat.id, ads, index, state)


async def prev_my_ad(message: types.Message, state: FSMContext, index: int):
    async with state.proxy() as data:
        ads = data.get('ads')
        if ads:
            index -= 1
            if index < 0:
                index = len(ads) - 1
            await send_my_ad(message.chat.id, ads, index, state)


async def send_my_ad(chat_id: int, ads: List[Ad], index: int, state: FSMContext):
    session = Session()
    ad = ads[index]
    user = session.query(User).filter(User.id == ad.user_id).first()
    session.close()

    ad_message = f"<b>Название:</b> {ad.title}\n" \
                 f"<b>Описание:</b> {ad.description}\n" \
                 f"<b>Дата:</b> {ad.date}\n" \
                 f"<b>Стоимость:</b> {ad.cost} ₽\n" \
                 f"<b>Локация:</b> {ad.location}\n" \
                 f"<b>Категория:</b> {ad.category}\n"
    buttons = [
        types.InlineKeyboardButton("⬅️", callback_data=f"prev_my_ad_{index}"),
        types.InlineKeyboardButton(f"{index + 1}/{len(ads)}", callback_data='ad_my_index'),
        types.InlineKeyboardButton("➡️", callback_data=f"next_my_ad_{index}")
    ]

    if ad.photo_url:
        message = await bot.send_photo(chat_id, ad.photo_url, caption=ad_message, parse_mode="HTML",
                                       reply_markup=types.InlineKeyboardMarkup().row(*buttons))
    else:
        message = await bot.send_message(chat_id, ad_message, parse_mode="HTML",
                                         reply_markup=types.InlineKeyboardMarkup().row(*buttons))

    await state.update_data(previous_message_id=message.message_id)  # Сохраняем ID сообщения в состоянии


@dp.callback_query_handler(full_timep_callback.filter(), state="*")
async def process_full_timepicker(callback_query: CallbackQuery, callback_data: dict, state: FSMContext):
    global save_counter
    r = await FullTimePicker().process_selection(callback_query, callback_data)

    date_info = await state.get_data()
    if r.selected:
        date = str(date_info.get('date'))[:11]
        a = r.time.strftime("%H:%M:%S")
        date += a
        date_object = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        await state.update_data(date=date_object)
        async with state.proxy() as data:
            photo_url = data.get('photo_url')
            title = data.get('title')
            description = data.get('description')
            cost = data.get('cost')
            location = data.get('location')
            ad = Ad(title=title, photo_url=photo_url, description=description, date=date_object, cost=cost, location=location)
            session = Session()
            session.add(ad)
            session.commit()
            session.close()
        success_message = await callback_query.message.answer('Дата объявления успешно сохранена!')
        save_counter += 1  #
        messages_to_delete = [callback_query.message, success_message]
        for i in range(1, 10):
            try:
                message_id = callback_query.message.message_id - i
                message = await bot.delete_message(chat_id=callback_query.message.chat.id, message_id=message_id)
                messages_to_delete.append(message)
            except aiogram.utils.exceptions.MessageToDeleteNotFound:
                pass
        await send_main_menu_for_new_ad(callback_query.message, state)
        # Удаление сообщений после отправки главного меню
        for message in messages_to_delete:
            try:
                await bot.delete_message(chat_id=callback_query.message.chat.id,
                                         message_id=callback_query.message.message_id)
            except aiogram.utils.exceptions.MessageToDeleteNotFound:
                pass
        await callback_query.message.delete_reply_markup()
