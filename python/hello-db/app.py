# encoding: UTF-8
import argparse

from typing import List, Any, Dict

## Веб сервер
import cherrypy

# Драйвер PostgreSQL
import psycopg2 as pg_driver
import psycopg2.pool as pool

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
    distance = DecimalField([Check('distance > 0.0')])
    name = TextField(unique=True)

    class Meta:
        database = db
        db_table = "planet"


class FlightEntity(Model):
    id = PrimaryKeyField()
    date = DateField()
    available_seats = IntegerField([Check('available_seats > 0')])
    planet = ForeignKeyField(PlanetEntity, related_name='flights')

    class Meta:
        database = db
        db_table = "flightentityview"


pg_pool = pool.SimpleConnectionPool(1, 100, user=args.pg_user, password=args.pg_password, host=args.pg_host, port=args.pg_port)


def getconn():
    return pg_driver.connect(user=args.pg_user, password=args.pg_password, host=args.pg_host, port=args.pg_port)


@cherrypy.expose
class App(object):
    flight_cache = ...  # type: Dict[int, FlightEntity]

    def __init__(self):
        self.flight_cache = dict()

    @cherrypy.expose
    def index(self):
        return "Привет. Тебе интересно сходить на /flights, /delete_planet или /delay_flights"

    def cache_flights(self, flight_date):
        flight_ids = []  # type: List[int]

        db = pg_pool.getconn()
        try:
            cur = db.cursor()
            if flight_date is None:
                cur.execute("SELECT id FROM Flight")
            else:
                print(flight_date)
                cur.execute("SELECT id FROM Flight WHERE date = %s", (flight_date,))
            flight_ids = [row[0] for row in cur.fetchall()]
        finally:
            pg_pool.putconn(db)

        # Now let's check if we have some cached data, this will speed up performance, kek
        for flight_id in flight_ids:
            if not flight_id in self.flight_cache:
                # OMG, cache miss! Let's fetch data
                flight = FlightEntity.select().join(PlanetEntity).where(FlightEntity.id == flight_id).get()
                if flight is not None:
                    self.flight_cache[flight_id] = flight

        return flight_ids

    # Отображает таблицу с полетами в указанную дату или со всеми полетами,
    # если дата не указана
    #
    # Пример: /flights?flight_date=2084-06-12
    #         /flights
    @cherrypy.expose
    def flights(self, flight_date=None):
        # Let's cache the flights we need
        flight_ids = self.cache_flights(flight_date)

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
        for flight_id in flight_ids:
            flight = self.flight_cache[flight_id]
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
        # Make sure flights are cached
        flight_ids = self.cache_flights(flight_date)

        # Update flights, reuse connections 'cause 'tis faster
        try:
            db = pg_pool.getconn()
            cur = db.cursor()
            for id in flight_ids:
                cur.execute("UPDATE Flight SET date=date + interval %s WHERE id=%s", (interval, id))
        finally:
            pg_pool.putconn(db)

    # Удаляет планету с указанным идентификатором.
    # Пример: /delete_planet?planet_id=1
    @cherrypy.expose
    def delete_planet(self, planet_id=None):
        if planet_id is None:
            return "Please specify planet_id, like this: /delete_planet?planet_id=1"
        db = pg_pool.getconn()
        try:
            cur = db.cursor()
            cur.execute("DELETE FROM Planet WHERE id = %s", (planet_id,))
        finally:
            pg_pool.putconn(db)


if __name__ == '__main__':
    cherrypy.quickstart(App())
