CREATE OR REPLACE FUNCTION GenerateSchema() RETURNS VOID AS $$
BEGIN
-- Справочник политических строев
CREATE TABLE Government(id SERIAL PRIMARY KEY, value TEXT UNIQUE);

-- Планета, её название, расстояние до Земли, политический строй
CREATE TABLE Planet(
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE,
  distance NUMERIC(5,2),
  government_id INT REFERENCES Government);

-- Значения рейтинга пилотов
CREATE TYPE Rating AS ENUM('Harmless', 'Poor', 'Average', 'Competent', 'Dangerous', 'Deadly', 'Elite');

-- Пилот корабля
CREATE TABLE Commander(
  id SERIAL PRIMARY KEY,
  name TEXT UNIQUE,
  rating Rating);

-- Космический корабль, вместимость пассажиров и класс корабля
CREATE TABLE Spacecraft(
  id SERIAL PRIMARY KEY,
  capacity INT CHECK(capacity > 0),
  name TEXT UNIQUE,
  class INT CHECK(class BETWEEN 1 AND 3));

-- Полет на планету в означеную дату, выполняемый кораблем, пилотируемый капитаном
CREATE TABLE Flight(id INT PRIMARY KEY,
  spacecraft_id INT REFERENCES Spacecraft,
  commander_id INT REFERENCES Commander,
  planet_id INT REFERENCES Planet ON DELETE CASCADE,
  date DATE
);

-- Стоимость полета до планеты на корабле означенного класса
CREATE TABLE Price(
  planet_id INT REFERENCES Planet ON DELETE CASCADE,
  spacecraft_class INT CHECK(spacecraft_class BETWEEN 1 AND 3),
  price INT CHECK(price>0),
  UNIQUE(planet_id, spacecraft_class));

-- Раса пассажира
CREATE TYPE Race AS ENUM('Elves', 'Men', 'Trolls');

-- Пассажир
CREATE TABLE Pax(
  id INT PRIMARY KEY,
  name TEXT,
  race Race);

-- Резервирование места на полет
CREATE TABLE Booking(
  ref_num TEXT PRIMARY KEY,
  pax_id INT REFERENCES Pax,
  flight_id INT REFERENCES Flight ON DELETE SET NULL);

CREATE OR REPLACE VIEW FlightEntityView  AS
SELECT T.fl_id as id, date, planet_id, capacity - COUNT(flight_id) AS available_seats
FROM (
         SELECT F.id AS fl_id, date, capacity, planet_id
         FROM Flight F JOIN Spacecraft S ON F.spacecraft_id = S.id
     ) T LEFT JOIN Booking B ON T.fl_id = B.flight_id GROUP BY T.fl_id, date, planet_id, capacity;
END;
$$ LANGUAGE plpgsql;

