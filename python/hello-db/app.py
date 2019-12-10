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

from psycopg2 import pool
pgpool = pool.SimpleConnectionPool(1, 20, user=args.pg_user, host=args.pg_host, password=args.pg_password, port=args.pg_port)


from contextlib import contextmanager

@contextmanager
def get_conn():
    conn = pgpool.getconn()
    try:
        yield conn
        conn.commit()
    finally:
        pgpool.putconn(conn)


# Классы ORM модели
class PlanetEntity(Model):
    id = PrimaryKeyField()
    distance = DecimalField()
    name = TextField()

    class Meta:
        database = db
        db_table = "planet"


class FlightEntity(Model):
    id = IntegerField()
    date = DateField()
    available_seats = IntegerField()
    planet = ForeignKeyField(PlanetEntity, related_name='flights')

    class Meta:
        database = db
        db_table = "flightentityview"


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
        # Полётов может быть очень много, когда у нас уже есть БД для их хранения.
        # К тому же, данные в кэше могут оказаться вдруг неактуальными.
        # Также проще получить сразу все данные из view, чем сначала получать id'шники.

        flights = None
        if not flight_date:
            flights = FlightEntity.select().join(PlanetEntity).execute()
        else:
            flights = FlightEntity.select().join(PlanetEntity).where(FlightEntity.date == flight_date).execute()

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
        for flight in flights:
            result_text += '<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(flight.id, flight.date,
                                                                                          flight.planet.name,
                                                                                          flight.planet.id)
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

        # Можно всё сделать в одном запросе.
        with get_conn() as conn:
            conn.cursor().execute("UPDATE Flight SET date=date + interval %s WHERE date=%s", (interval, flight_date))

    # Удаляет планету с указанным идентификатором.
    # Пример: /delete_planet?planet_id=1
    @cherrypy.expose
    def delete_planet(self, planet_id=None):
        if planet_id is None:
            return "Please specify planet_id, like this: /delete_planet?planet_id=1"

        with get_conn() as conn:
            conn.cursor().execute("DELETE FROM Planet WHERE id = %s", (planet_id,))
            

if __name__ == '__main__':
    cherrypy.quickstart(App())
