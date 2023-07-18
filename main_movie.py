import json
import logging
import random
import time as t
import requests
from bs4 import BeautifulSoup
from sqlalchemy import create_engine, Column, ForeignKey, Integer, String, Text, Date, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from urllib.parse import urlparse, parse_qs, urlunparse
from datetime import date, timedelta
from random import randint
#from test12 import jsonchik


def parsing_yandex_afisha(city):
    with open('city.json', encoding='utf-8') as json_file:
        cities = json.load(json_file)

    header = {
        'Accept': '*/*',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 '
                      f'Safari/{random.randint(10, 99)}.36',
        'Accept-Language': 'ru',
        'Connection': 'keep-alive',
        'Content-Type': 'text/plain;charset=UTF-8'
    }

    response = requests.get(cities[city.title()], headers=header)

    soup = BeautifulSoup(response.text, 'html.parser')
    all_cinema_link = []
    all_cinema = soup.find_all('div', class_='event events-list__item yandex-sans')
    for i in all_cinema:
        all_cinema_link.append('https://afisha.yandex.ru' + i.find('a', class_='EventLink-sc-1x07jll-2').get(
            'href'))

    cleaned_links = []  # массив со ссылками без параметра schedule-date
    today = date.today()
    print('Процесс парсинга пошел')
    print(all_cinema_link)

    data = {'all_info': []}
    c = 0
    if all_cinema_link:
        for link in all_cinema_link:
            try:
                header = {
                    'Accept': '*/*',
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 '
                                  f'Safari/{random.randint(10, 99)}7.36',
                    'Accept-Language': 'ru',
                    'Connection': 'keep-alive',
                    'Content-Type': 'text/plain;charset=UTF-8'
                }
                t.sleep(random.randint(2, 6))
                res = requests.get(link, headers=header)
                soup2 = BeautifulSoup(res.text, 'html.parser')

                title = soup2.find('div', class_='event-concert-description__title-info').text
                img = soup2.find('img', class_='image event-concert-heading__poster').get('src')
                genre = soup2.find_all('li', class_='tags__item')[1].text  # Жанр
                about = soup2.find('div', class_='concert-description__text-wrap').text

                country = 'Страна не указана'
                time = 'Продолжительность не указана'
                for i in soup2.find_all('div', class_='event-attributes__row'):
                    if i.find('dt', class_='event-attributes__category').text == 'Страна':
                        country = i.find('dd', class_='event-attributes__category-value').text
                    if i.find('dt', class_='event-attributes__category').text == 'Время':
                        time = i.find('dd', class_='event-attributes__category-value').text

                session = {'all_sessions': []}
                all_cinema_name = []
                session_time = []
                for d in range(7):
                    t.sleep(random.randint(1, 3))
                    next_day = today + timedelta(days=d)
                    formatted_date = next_day.strftime("%Y-%m-%d")
                    parsed = urlparse(link)
                    params = parse_qs(parsed.query)
                    params.pop('schedule-date', None)
                    cleaned_query = '&'.join(key + '=' + value[0] for key, value in params.items())
                    cleaned_url = urlunparse(parsed._replace(query=cleaned_query))
                    cleaned_links.append(cleaned_url + f'&schedule-date={formatted_date}')

                    res = requests.get(link, headers=header)
                    soup2 = BeautifulSoup(res.text, 'html.parser')

                    for i in soup2.find_all('div', class_='Wrapper-sc-1b6srcd-1'):

                        all_cinema_name.append(i.find('span', class_='NameOuter-sc-1trqzwk-1').text.replace(u'\xa0', u''))
                        session_time1 = []
                        for y in i.find_all('span', class_='ButtonEmpty-d2ik01-1'):
                            session_time1.append(y.text)

                        for p in i.find_all('span', class_='Text-sc-19jb13r-1'):
                            session_time1.append(p.text)
                        session_time.append(session_time1)

                        session['all_sessions'].append({
                            'date': formatted_date,
                            'info': {
                                'cinema': all_cinema_name[-1],
                                's_time': session_time[-1],
                                     }
                        })

                    all_info = {
                        'title': title,
                        'img': img,
                        'genre': genre,
                        'about': about,
                        'country': country,
                        'time': time,
                        'session': {
                            "cinema": "Нет кинотеатров, которые бы показывали бы данное кино",
                            "time": ["К сожалению сеансов нет"]
                        } if session == {} else session,
                    }
                c += 1
                print(f'Готово {c} из {len(all_cinema_link)}')
                data['all_info'].append(all_info)
            except AttributeError:
                continue
    else:
        print('К сожалению сраный яндекс нас забанил')
    return data


def add_data_to_postgres(city):
    db_url = 'postgresql://bot_market:3jv6ETm2z2fSM9Mo7Pfh@80.89.239.246:5432/bot_market'
    engine = create_engine(db_url)
    base = declarative_base()
    today = date.today()

    class Movie(base):
        __tablename__ = 'Movie'

        id = Column(Integer, primary_key=True)
        title = Column(String(200), nullable=False)
        img = Column(Text(), nullable=False)
        genre = Column(String(50), nullable=False)
        about = Column(Text(), nullable=False)
        country = Column(String(50), nullable=False)
        time = Column(String(50), nullable=False)
        city_id = Column(Integer, ForeignKey("City.id", ondelete='CASCADE'))
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

    # Привязываем таблицы к движку
    base.metadata._bind = engine

    # Создаем сессию
    session1 = sessionmaker(bind=engine)
    session = session1()

    inspector = inspect(engine)

    # Проверяем существование таблиц
    movie_table_exists = inspector.has_table('Movie')
    city_table_exists = inspector.has_table('City')
    cinema_table_exists = inspector.has_table('Cinema')
    response_date_table_exists = inspector.has_table('Response_Date')

    # Если таблицы не существуют, создаем их
    if not (movie_table_exists and city_table_exists and cinema_table_exists and response_date_table_exists):
        base.metadata.create_all(engine)
    else:
        city_exists = session.query(City).filter_by(name=city.title()).first()

        date_exists = session.query(ResponseDate).first()
        if date_exists is not None:
            # Разделяем строку на компоненты года, месяца и дня
            year1, month1, day1 = map(int, str(today).split('-'))
            year2, month2, day2 = map(int, str(date_exists.res_date).split('-'))

            td = date(year1, month1, day1)
            # td = date(2023, 7, 30)  # Это для удаления
            tm_bd = date(year2, month2, day2)
            if (td - tm_bd).days >= 7:
                session.close()
                logging.warning('Идет очистка базы данных')
                # base.metadata.drop_all(bind=engine, cascade=True)
                Cinema.__table__.drop(engine)
                Movie.__table__.drop(engine)
                City.__table__.drop(engine)
                ResponseDate.__table__.drop(engine)
                logging.warning('База данных очищена')
                logging.warning('Сделайте запрос еще раз')
                return
        if city_exists:
            session.close()
            logging.warning('Данный город уже записан в бд')
            return 0

    # Создаем и добавляем записи данных
    data = parsing_yandex_afisha(city.title())['all_info']
    # data = jsonchik()['all_info']
    # Проверяем количество записей в таблице ResponseDate
    count = session.query(ResponseDate).count()

    # Если количество записей равно 1, то не создаем новую запись
    if count < 1:
        # Создаем запись в таблице Response_Date со значением сегодняшней даты
        response = ResponseDate(res_date=today)
        session.add(response)

    cit = City(
        name=city.title()
    )

    for cin in data:
        movie = Movie(title=cin['title'], img=cin['img'], genre=cin['genre'], about=cin['about'],
                      country=cin['country'], time=cin['time'], city=cit)
        session.add(movie)

        for ses in cin['session']['all_sessions']:
            cinema = Cinema(name=ses['info']['cinema'], time=ses['info']['s_time'], date=ses['date'], movie=movie)
            session.add(cinema)

    session.add(cit)

    # Сохраняем изменения в базе данных
    session.commit()

    # Закрываем сессию
    session.close()

    return 0
