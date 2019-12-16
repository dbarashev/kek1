CREATE OR REPLACE FUNCTION GenerateSchema() RETURNS VOID AS $$
BEGIN
-- Справочник политических строев
CREATE TABLE Government(id SERIAL PRIMARY KEY, value TEXT UNIQUE);


--- основные изменения -- это добавление NOT NULL + is not null в view


-- Планета, её название, расстояние до Земли, политический строй
CREATE TABLE Planet(
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  distance NUMERIC(5,2) NOT NULL,
  government_id INT REFERENCES Government);

-- Значения рейтинга пилотов
CREATE TYPE Rating AS ENUM('Harmless', 'Poor', 'Average', 'Competent', 'Dangerous', 'Deadly', 'Elite');

-- Пилот корабля
CREATE TABLE Commander(
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  rating Rating NOT NULL);

-- Космический корабль, вместимость пассажиров и класс корабля
CREATE TABLE Spacecraft(
  id SERIAL PRIMARY KEY,
  capacity INT NOT NULL CHECK(capacity > 0),
  name TEXT NOT NULL UNIQUE,
  class INT NOT NULL CHECK(class BETWEEN 1 AND 3));

-- Полет на планету в означеную дату, выполняемый кораблем, пилотируемый капитаном
CREATE TABLE Flight(id INT PRIMARY KEY,
  spacecraft_id INT REFERENCES Spacecraft,
  commander_id INT REFERENCES Commander,
  planet_id INT REFERENCES Planet ON DELETE CASCADE,
  date DATE NOT NULL
);

-- Стоимость полета до планеты на корабле означенного класса
CREATE TABLE Price(
  planet_id INT REFERENCES Planet ON DELETE CASCADE,
  spacecraft_class INT NOT NULL CHECK(spacecraft_class BETWEEN 1 AND 3),
  price INT NOT NULL CHECK(price>0),
  UNIQUE(planet_id, spacecraft_class));

-- Раса пассажира
CREATE TYPE Race AS ENUM('Elves', 'Men', 'Trolls');

-- Пассажир
CREATE TABLE Pax(
  id INT PRIMARY KEY,
  name TEXT NOT NULL,
  race Race NOT NULL);

-- Резервирование места на полет
CREATE TABLE Booking(
  ref_num TEXT PRIMARY KEY,
  pax_id INT NOT NULL REFERENCES Pax,
  flight_id INT REFERENCES Flight ON DELETE SET NULL);   --- тут по идее можно наверное потом добавить новый полет и обновить
--- а можно и удалить как со всеми остальными, но пусть будет так -- тогда добавим условие в view ниже, что хотим не нулевые flight_id

CREATE OR REPLACE VIEW FlightAvailableSeatsView AS
SELECT flight_id, capacity - booked_seats AS available_seats
FROM (
         SELECT F.id AS flight_id, date, capacity, (SELECT COUNT(*) FROM Booking WHERE flight_id=F.id and flight_id IS NOT NULL) AS booked_seats
         FROM Flight F JOIN Spacecraft S ON F.spacecraft_id = S.id
     ) T;

CREATE OR REPLACE VIEW FlightEntityView AS
SELECT id, date, available_seats, planet_id
FROM Flight F JOIN FlightAvailableSeatsView S ON F.id = S.flight_id;

END;
$$ LANGUAGE plpgsql;

