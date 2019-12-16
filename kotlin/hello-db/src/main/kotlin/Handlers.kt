package hellodb

import java.math.BigDecimal
import java.util.*
import javax.persistence.*


@Entity(name = "planet")
class PlanetEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Int? = null
    var name: String? = null
    var distance: BigDecimal? = null
    @OneToMany(fetch = FetchType.EAGER, mappedBy = "planet")
    var flights: List<FlightEntity>? = null
}

@Entity(name = "flightentityview")
class FlightEntity {
    @Id
    var id: Int? = null
    var date: Date? = null
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "planet_id")
    var planet: PlanetEntity? = null
}

class FlightDto {
    var flight_id: Int? = null
    var date: Date? = null
    var planet_name: String? = null
    var planet_id: Int? = null
}

class FlightsHandler() {
    //    private val flightCache = mutableMapOf<Int, FlightEntity>()
    private val emf = Persistence.createEntityManagerFactory("Postgres")
//    private val entityManager = emf.createEntityManager()

    fun handleFlights(flightDate: Date?): String {
        // тут мы ходим в "кеш", достаем данные из базы данных, кладем недостающие данные в кеш.
        // и потом опть их достаем из кеша и возвращаем построчно назад
        // лучше избавиться от кеша и доставать данные каждый раз пачкой из view
        val tablebody = getFlightIdByData(flightDate)
        val result = getDataFromView(tablebody)
                .map { """<tr><td>${it.flight_id}</td><td>${it.date}</td><td>${it.planet_name}</td><td>${it.planet_id}</td></tr>""" }
                .joinToString(separator = "\n")
        return "$FLIGHTS_HEADER $result $FLIGHTS_FOOTER"
    }

    fun handleDelayFlights(flightDate: Date, interval: String): String {
        var updateCount = 0
        // здесь плохо ходить на каждый update в бд и апдейтить
//        cacheFlights(flightDate).forEach { flightId ->
//            withConnection(true) {
//                updateCount += it.prepareStatement("UPDATE Flight SET date=date + interval '$interval' WHERE id=$flightId")
//                        .executeUpdate()
//            }
//        }
        withConnection(true) {
            updateCount +=
                    it.prepareStatement(
                            "UPDATE Flight SET date=date + interval '$interval' WHERE date=$flightDate")
                            .executeUpdate()
        }
        return "Updated $updateCount flights"
    }


    fun handleDeletePlanet(planetId: Int): String {
        val deleteCount = withConnection(true) {
            // я не уверена, какая-то очевидная ошибка по сравнению с остальными. false -> true
            // и тут просто так удалить планету по id не получится.
            // Потому что на планету ссылаются flight и price, а на flight таблиуа booking.
            // Вообще не понятно легально ли это делать с точки бизнес логики.
            it.prepareStatement("DELETE FROM Planet WHERE id=?").also { stmt ->
                stmt.setInt(1, planetId)
            }.executeUpdate()
        }
        return "Deleted $deleteCount planets"
    }


    private fun getFlightIdByData(flightDate: Date?): List<Int> {
        val flightIds = mutableListOf<Int>()
        withConnection(true) {
            if (flightDate == null) {
                it.prepareStatement("SELECT id FROM Flight")
            } else {
                it.prepareStatement("SELECT id FROM Flight WHERE date=?").also { stmt ->
                    stmt.setDate(1, java.sql.Date(flightDate.time))
                }
            }.use {
                it.executeQuery().use { resultSet ->
                    while (resultSet.next()) {
                        //тут  зачем-то сохраняется в кеш каждый раз строка из flightentityview
                        val flightId = resultSet.getInt("id")
//                        if (!this.flightCache.containsKey(flightId)) {
//                            val flightEntity = entityManager.find(FlightEntity::class.java, flightId)
//                            if (flightEntity != null) {
//                                this.flightCache[flightId] = flightEntity
//                            }
//                        }
                        flightIds.add(flightId)
                    }
                }
            }
        }
        return flightIds
    }

    private fun getDataFromView(flightIds: List<Int>): List<FlightDto> {
        val result = mutableListOf<FlightDto>()
        withConnection(true) {
            it.prepareStatement("SELECT f.id as flight_id , f.date as date, p.name as planet_name, p.id as planet_id " +
                    "FROM flightentityview f " +
                    "inner join planet p on f.planet_id = p.id " +
                    "where f.id in (" + flightIds.joinToString(separator = ",") + ")")
                    .executeQuery()
                    .use { resultSet ->
                        while (resultSet.next()) {
                            val v = FlightDto();
                            v.date = resultSet.getDate("date");
                            v.flight_id = resultSet.getInt("flight_id");
                            v.planet_name = resultSet.getString("planet_name");
                            v.planet_id = resultSet.getInt("planet_id");
                            result.add(v);
                        }
                    }
        }
        return result;
    }
}

private const val FLIGHTS_HEADER = """
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

private const val FLIGHTS_FOOTER = """
        </table>
        </body>
        </html>"""
