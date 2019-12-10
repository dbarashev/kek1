# encoding: UTF-8
import argparse
import contextlib
import sys

from typing import List, Any, Dict

## Веб сервер
import cherrypy

# Драйвер PostgreSQL
from psycopg2.pool import SimpleConnectionPool

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
parser.add_argument('--pg-password', help='PostgreSQL password', default='')
parser.add_argument('--pg-database', help='PostgreSQL database', default='postgres')

args = parser.parse_args()

db = PostgresqlDatabase(args.pg_database, user=args.pg_user, host=args.pg_host, password=args.pg_password)


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


pool = SimpleConnectionPool(minconn=1, maxconn=10, user=args.pg_user, password=args.pg_password, host=args.pg_host, port=args.pg_port, database=args.pg_database)


@contextlib.contextmanager
def getconn():
    conn = pool.getconn()
    try:
        yield conn
    finally:
        pool.putconn(conn)


@cherrypy.expose
class App(object):

    def __init__(self):
        self.flight_cache = dict()

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
        # Let's cache the flights we need
        data = self.get_flights_for_date(flight_date)

        # Okeyla, now let's format the result HTML

        header = """
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
        result = [header]
        for flight in data:
            result.append('<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>'.format(flight.id, flight.date,
                                                                                         flight.planet.name,
                                                                                         flight.planet.id)
                          )

        footer = """
        </table>
        </body>
        </html>"""
        result.append(footer)
        cherrypy.response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return ''.join(result)

    def get_flights_for_date(self, flight_date):
        flights = FlightEntity.select()
        if flight_date is not None:
            flights = flights.where(FlightEntity.date == flight_date)
        flights = flights.join(PlanetEntity)
        # типа логированние в дебаг режиме
        print(flights.sql(), file=sys.stderr)
        data = flights.execute()
        return data

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
        flights = self.get_flights_for_date(flight_date)

        with getconn() as db:
            cur = db.cursor()
            for f in flights:
                cur.execute("UPDATE Flight SET date=date + interval %s WHERE id=%s", (interval, f.id))

    # Удаляет планету с указанным идентификатором.
    # Пример: /delete_planet?planet_id=1
    @cherrypy.expose
    def delete_planet(self, planet_id=None):
        if planet_id is None:
            return "Please specify planet_id, like this: /delete_planet?planet_id=1"
        with getconn() as db:
            cur = db.cursor()
            cur.execute("DELETE FROM Planet WHERE id = %s", (int(planet_id),))


if __name__ == '__main__':
    cherrypy.quickstart(App())
