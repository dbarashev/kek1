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

class FlightsHandler() {
  private val flightCache = mutableMapOf<Int, FlightEntity>()
  private val emf = Persistence.createEntityManagerFactory("Postgres")
  private val entityManager = emf.createEntityManager()

  fun handleFlights(flightDate: Date?) : String {
    val tablebody = cacheFlights(flightDate).map { flightCache[it] }.filterNotNull().map {
      """<tr><td>${it.id}</td><td>${it.date}</td><td>${it.planet?.name}</td><td>${it.planet?.id}</td></tr>"""
    }.joinToString(separator = "\n")
    return "$FLIGHTS_HEADER $tablebody $FLIGHTS_FOOTER"
  }

  fun handleDelayFlights(flightDate: Date, interval: String) : String {
    var updateCount = 0
    cacheFlights(flightDate).forEach { flightId ->
      withConnection(true) {
        updateCount += it.prepareStatement("UPDATE Flight SET date=date + interval '$interval' WHERE id=$flightId")
            .executeUpdate()
      }
    }
    return "Updated $updateCount flights"
  }


  fun handleDeletePlanet(planetId: Int) : String {
    val deleteCount = withConnection(false) {
      it.prepareStatement("DELETE FROM Planet WHERE id=?").also { stmt ->
        stmt.setInt(1, planetId)
      }.executeUpdate()
    }
    return "Deleted $deleteCount planets"
  }



  private fun cacheFlights(flightDate: Date?) : List<Int> {
    val flightIds = mutableListOf<Int>()
    withConnection(true) {
      if (flightDate == null) {
        it.prepareStatement("SELECT id FROM Flight")
      } else {
        it.prepareStatement("SELECT id FROM Flight WHERE date=?").also {stmt ->
          stmt.setDate(1, java.sql.Date(flightDate.time))
        }
      }.use {
        it.executeQuery().use {resultSet ->
          while (resultSet.next()) {
            val flightId = resultSet.getInt("id")
            if (!this.flightCache.containsKey(flightId)) {
              val flightEntity = entityManager.find(FlightEntity::class.java, flightId)
              if (flightEntity != null) {
                this.flightCache[flightId] = flightEntity
              }
            }
            flightIds.add(flightId)
          }
        }
      }
    }
    return flightIds
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
