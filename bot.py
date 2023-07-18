from datetime import datetime
import aiogram
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.exceptions import BadRequest
from aiogram_calendar import SimpleCalendar, simple_cal_callback
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Date
from main_movie import add_data_to_postgres
from models import User

TOKEN = "6148131942:AAEpn5TLBNQhR1yhq5yLlCPgu75MphO_aVw"
DATABASE_URL = "postgresql://bot_market:3jv6ETm2z2fSM9Mo7Pfh@80.89.239.246:5432/bot_market"
base = declarative_base()


class Movie(base):
    __tablename__ = 'Movie'

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    img = Column(Text(), nullable=False)
    genre = Column(String(50), nullable=False)
    about = Column(Text(), nullable=False)
    country = Column(String(50), nullable=False)
    time = Column(String(50), nullable=False)
    city_id = Column(Integer, ForeignKey("City.id"))
    city = relationship("City")
    cinemas = relationship("Cinema")


class City(base):
    __tablename__ = 'City'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    movies = relationship("Movie")


class Cinema(base):
    __tablename__ = 'Cinema'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    time = Column(Text(), nullable=False)
    date = Column(Date, nullable=False)
    movie_id = Column(Integer, ForeignKey("Movie.id"))
    movie = relationship("Movie")


class ResponseDate(base):
    __tablename__ = 'Response_Date'

    id = Column(Integer, primary_key=True)
    res_date = Column(Date, nullable=False)


bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class FsmAdmin(StatesGroup):
    city = State()
    cin = State()
    mas = State()


engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()


@dp.message_handler(commands=['start'])
async def start(message: types.Message, state: FSMContext):
    global save_counter  # Объявляем глобальную переменную
    save_counter = 0
    print(save_counter)
    await state.finish()
    user_id = message.from_user.id
    username = message.from_user.username
    session = Session()
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, username=username)
        session.add(user)
    if user.username != username:
        user.username = username
    session.commit()
    session.close()
    await show_main_menu(message)


async def show_main_menu(message: types.Message):
    global save_counter  # Объявляем глобальную переменную
    save_counter = 0
    print(save_counter)
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton('🎥 Кино', callback_data='movie'))  # #просмотр категорий тут кино
    keyboard.add(types.InlineKeyboardButton('🗓 Другое', callback_data='view_other'))
    await message.answer('📍 Главное меню', reply_markup=keyboard)
    # await States.main_menu.set()


@dp.callback_query_handler(lambda callback_query: callback_query.data == 'movie')
async def search_movies_by_city(callback_query: types.CallbackQuery):
    global save_counter  # Объявляем глобальную переменную
    save_counter = 0
    print(save_counter)
    user = session.query(User).filter_by(id=callback_query.message.chat.id).first()
    if user:
        city = session.query(City).filter_by(id=user.city_id).first()
        if city:
            cinemas = session.query(Cinema).join(Movie).filter(Movie.city_id == city.id).filter(
                Cinema.movie_id == Movie.id).all()
            if cinemas:
                cinema_names = list(set([cinema.name for cinema in cinemas]))
                inline_buttons = [InlineKeyboardButton(
                    text=name, callback_data=f'cinema_{name}') for name in cinema_names]
                inline_buttons.append(InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_menu'))  # Add
                # back button
                markup = InlineKeyboardMarkup(row_width=2).add(*inline_buttons)

                await callback_query.message.answer(f"🎥 Выберите кинотеатр в городе {city.name} ", reply_markup=markup)
            else:
                await callback_query.message.reply("🤖 К сожалению, в данном городе сеансов кино не найдено.")
        else:
            await callback_query.message.reply("К сожалению, город не найден в базе данных")
    else:
        await callback_query.message.reply("К сожалению, информация о пользователе не найдена.")


@dp.callback_query_handler(lambda callback_query: callback_query.data == 'back_to_menu')
async def back_to_menu(callback_query: types.CallbackQuery):
    await callback_query.answer()
    await show_main_menu(callback_query.message)
    await callback_query.message.delete()


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('city_'))
async def select_city(callback_query: types.CallbackQuery):
    city_name = callback_query.data.split('_')[1]
    await callback_query.answer()
    a = add_data_to_postgres(city_name)
    if a == 0:
        city = session.query(City).filter_by(name=city_name).first()
        cinemas = session.query(Cinema).join(Movie).filter(
            Movie.city_id == city.id).filter(Cinema.movie_id == Movie.id).all()
        if cinemas:
            cinema_names = list(set([cinema.name for cinema in cinemas]))
            inline_buttons = [InlineKeyboardButton(text=name, callback_data=f'cinema_{name}') for name in cinema_names]
            markup = InlineKeyboardMarkup(row_width=2).add(*inline_buttons)
            await callback_query.message.answer("Выберите кинотеатр:", reply_markup=markup)
        else:
            await callback_query.message.reply("К сожалению, в данном городе сеансов кино не найдено.")
    else:
        await callback_query.message.reply("К сожалению, информации о кино в вашем городе нет или возникла ошибка.")


@dp.message_handler(state=FsmAdmin.city)
async def search_movies(message: types.Message, state: FSMContext):
    city_name = message.text.title()
    await state.update_data(city=city_name)
    city = session.query(City).filter_by(name=city_name).first()
    if city:
        cinemas = session.query(Cinema).join(Movie).filter(Movie.city_id == city.id).filter(Cinema.movie_id ==
                                                                                            Movie.id).all()
        if cinemas:
            cinema_name = []
            for cinema in cinemas:
                cinema_name.append(cinema.name)
            # Создаем список списков с кнопками
            inline_buttons = []
            for cinema in set(cinema_name):
                inline_buttons.append(InlineKeyboardButton(text=cinema, callback_data=f'cinema_{cinema}'))
            # Создаем InlineKeyboardMarkup с кнопками
            markup = InlineKeyboardMarkup(row_width=2).add(*inline_buttons)
            # Отправляем сообщение с кнопками пользователю
            await message.answer("Выберите кинотеатр:", reply_markup=markup)
            if not cinema_name:
                session.close()
                await message.answer(f'Кинотеатров нет')
        else:
            session.close()

            await message.answer("К сожалению, в данном городе сеансов кино не найдено.",
                                 )
    else:
        await state.finish()
        await message.answer("К сожалению в нашей базе данных нет этого города", reply_markup=InlineKeyboardMarkup(
        ).add(
            InlineKeyboardButton(text='Ввести еще раз ', callback_data='movie_again')
        ))
    await state.finish()
    await state.update_data(city=city_name)


@dp.callback_query_handler(lambda callback_query: callback_query.data.startswith('cinema_'))
async def select_cinema(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    # Получаем название кинотеатра из колбека
    cinema_name = callback_query.data.split('_')[1]
    await state.update_data(cin=cinema_name)
    # Создаем инлайн с календарем
    calendar_markup = await SimpleCalendar().start_calendar()

    back_button = InlineKeyboardButton('⬅️ Назад', callback_data='back_to_city')
    calendar_markup.add(back_button)  # Add the back button to the calendar markup

    await callback_query.message.answer("Выберите дату", reply_markup=calendar_markup)


@dp.callback_query_handler(text='back_to_city')
async def back_to_city(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    await search_movies_by_city(callback_query)


@dp.callback_query_handler(simple_cal_callback.filter())
async def process_simple_calendar(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    try:
        # Получаем выбранную дату из callback_data
        selected_date = datetime.strptime(
            callback_query.data.split(':')[2] + '-' + callback_query.data.split(':')[3] + '-' +
            callback_query.data.split(':')[4], '%Y-%m-%d').date()
        data1 = await state.get_data()
        cin1 = data1.get("cin")

        # Запрос для получения кинотеатров на выбранную дату
        cinemas = session.query(Cinema).join(Movie).filter(Cinema.date == selected_date,
                                                           Cinema.name == cin1).all()
        movies = session.query(Movie).join(Cinema).filter(Cinema.date == selected_date,
                                                          Cinema.name == cin1).all()

        if cinemas:
            instruction_caption = {'info': [], 'img': []}
            for movie in movies:
                raspisanie = session.query(Cinema).filter(Cinema.date == selected_date,
                                                          Cinema.name == cin1,
                                                          Cinema.movie_id == movie.id).all()
                a = [i.time for i in raspisanie]
                kino = [i.name for i in raspisanie]
                text = f"✅ Название: {movie.title}\n" \
                       f"✒️ Жанр: {movie.genre}\n" \
                       f"🗒 Описание: {movie.about}\n" \
                       f"🗺 Страна: {movie.country}\n" \
                       f"⏳ Время: {movie.time}\n" \
                       f'📅 Выбранная дата: {selected_date}\n' \
                       f'🍿 Кинотеатр: {kino[0]}\n' \
                       f'🧾 Сеансы: {a[0]}\n'
                instruction_caption['info'].append(text)
                instruction_caption['img'].append(movie.img)

            text = instruction_caption['info'][0]
            await state.update_data(mas='')
            await state.update_data(mas=instruction_caption)

            back_button = InlineKeyboardButton('⬅️ Назад к выбору кинотеатра', callback_data='back_to_city')
            keyboard = construct_keyboard(instruction_caption, 1)

            calendar_markup = await SimpleCalendar().start_calendar()
            calendar_markup.row(back_button)

            await bot.send_photo(callback_query.message.chat.id, movies[0].img, caption=text, reply_markup=keyboard)
            session.close()
        else:
            await callback_query.message.reply(f'На выбранную дату нет данных о кинотеатрах')
    except BadRequest:
        calendar_markup = await SimpleCalendar().start_calendar()
        back_button = InlineKeyboardButton('⬅️ Назад', callback_data='back_to_city')
        calendar_markup.row(back_button)
        await callback_query.message.answer("К сожалению сеансов на выбранную дату нет, попробуйте снова",
                                            reply_markup=calendar_markup)


@dp.callback_query_handler(text_startswith='page_')
async def page(call: types.CallbackQuery, state: FSMContext):
    if call.data != 'back123':
        datas = await state.get_data()

        instruction_caption = datas.get("mas")
        page = int(call.data.split('_')[1])
        text = instruction_caption['info'][page]
        print(instruction_caption['info'])

        await call.answer()

        if page == 1:
            text = instruction_caption['info'][0]
            await bot.send_photo(call.message.chat.id, instruction_caption['img'][0], caption=text,
                                 reply_markup=construct_keyboard(instruction_caption, 1))
        else:
            await bot.send_photo(call.message.chat.id, instruction_caption['img'][page], caption=text,
                                 reply_markup=construct_keyboard(instruction_caption, page))
        await call.message.delete()


@dp.callback_query_handler(state='*', text='back123')
async def cancel_handler(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()
    print(callback_query)

    calendar_markup = await SimpleCalendar().start_calendar()
    await callback_query.message.answer("Выберите дату ", reply_markup=calendar_markup)

    current_state = await state.get_state()
    if current_state is None:
        return


def construct_keyboard(data: dict, page: int):
    length = len(data['img']) - 1
    buttons = []
    if page > 1:  # убираем возможность уйти в минус
        buttons.append(InlineKeyboardButton(text='⬅️', callback_data=f'page_{page - 1}'))

    buttons.append(InlineKeyboardButton(text=f'{page}/{length}', callback_data=f'none'))
    if page < length:  # проверка чтобы не выйти за границы листа
        buttons.append(InlineKeyboardButton(text='➡️', callback_data=f'page_{page + 1}'))

    kb = InlineKeyboardMarkup(row_width=3).row(*buttons).add(InlineKeyboardButton(
        '⬅️ Назад к выбору кинотеатра', callback_data='back_to_city'))
    return kb


if __name__ == '__main__':
    aiogram.executor.Executor(dp).start_polling()
