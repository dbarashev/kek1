# encoding: UTF-8
import argparse

from typing import List, Any, Dict

## Веб сервер
import cherrypy

# Драйвер PostgreSQL
import psycopg2 as pg_driver

# ORM
from peewee import *

# import logging
# logger = logging.getLogger('peewee')
# logger.addHandler(logging.StreamHandler())
# logger.setLevel(logging.DEBUG)

parser = argparse.ArgumentParser(description='Hello DB web application')
parser.add_argument('--pg-host', help='PostgreSQL host name', default='localhost')
parser.add_argument('--pg-port', help='PostgreSQL port', default=5432)
parser.add_argument('--pg-user', help='PostgreSQL user', default='postgres')
parser.add_argument('--pg-password', help='PostgreSQL password', default='postgres')
parser.add_argument('--pg-database', help='PostgreSQL database', default='postgres')

args = parser.parse_args()

db = PostgresqlDatabase(args.pg_database, user=args.pg_user, host=args.pg_host, password=args.pg_password)


def getconn():
    return pg_driver.connect(user=args.pg_user, password=args.pg_password, host=args.pg_host, port=args.pg_port)

"""
Комментарии:

1. flight_cache 
При создании полёта каждый раз делает запрос с join. При малом кол-ве полетов ок, при большом количестве будут тормоза. 
+ этот кэш не чистится. При изменении в полетах (пр. удалении) отображаются некорректные данные.

2. Обновление. Производится для каждой строки полета в определенную дату. Соотв. чтений столько, сколько полетов в дату.
Можно обновить одним запросом, выбирающим данные сразу по дате. 

3. + есть сомнения в конструкции with getconn(). Действительно ли соединение будет закрыто. Но в delete интуитивно исправила.
Возможно, надо было исправить всё по-другому"""

@cherrypy.expose
class App(object):

    @cherrypy.expose
    def index(self):
        return "Привет. Тебе интересно сходить на /flights, /delete_planet или /delay_flights"

    # Отображает таблицу с полетами в указанную дату или со всеми полетами,
    # если дата не указана
    #
    # Пример: /flights?flight_date=2084-06-12
    #         /flights
    @cherrypy.expose
    def flights(self, flight_date=None):

        # Okeyla, now let's format the result HTML
        result_text = """
        <html>
        <body>
        <style>
    table > * {
        text-align: left;
    }
    td {
        padding: 5px;
    }
    table { 
        border-spacing: 5px; 
        border: solid grey 1px;
        text-align: left;
    }
        </style>
        <table>
            <tr><th>Flight ID</th><th>Date</th><th>Planet</th><th>Planet ID</th></tr>
        """
        with getconn() as db:
            cur = db.cursor()
            if flight_date is None:
                cur.execute("SELECT f.id as id, f.date, p.name, p.id "
                            "FROM Flight f "
                            "JOIN Planet p "
                            "ON f.planet_id=p.id;")
            else:
                cur.execute("SELECT f.id as id, f.date, p.name, p.id "
                            "FROM Flight f "
                            "JOIN Planet p "
                            "ON f.planet_id=p.id "
                            "WHERE f.date = %s", (flight_date,))
            flights = cur.fetchall()

        for f in flights:
            result_text += '<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(f[0], f[1],
                                                                                          f[2],
                                                                                          f[3])
        result_text += """
        </table>
        </body>
        </html>"""
        cherrypy.response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return result_text

    # Сдвигает полёты, начинающиеся в указанную дату на указанный интервал.
    # Формат даты: yyyy-MM-dd (например 2019-12-19)
    # Формат интервала: 1day, 2weeks, и так далее.
    # https://www.postgresql.org/docs/current/datatype-datetime.html#DATATYPE-INTERVAL-INPUT
    #
    # пример: /delay_flights?flight_date=2084-06-12&interval=1day
    @cherrypy.expose
    def delay_flights(self, flight_date=None, interval=None):
        if flight_date is None or interval is None:
            return "Please specify flight_date and interval arguments, like this: /delay_flights?flight_date=2084-06-12&interval=1week"
        # Make sure flights are cached

        with getconn() as db:
            cur = db.cursor()
            cur.execute("UPDATE Flight SET date=date + interval %s WHERE date=%s", (interval, flight_date))

    # Удаляет планету с указанным идентификатором.
    # Пример: /delete_planet?planet_id=1
    @cherrypy.expose
    def delete_planet(self, planet_id=None):
        if planet_id is None:
            return "Please specify planet_id, like this: /delete_planet?planet_id=1"
        with getconn() as db:
            cur = db.cursor()
            cur.execute("DELETE FROM Planet WHERE id = %s", (planet_id,))


if __name__ == '__main__':
    cherrypy.quickstart(App())
