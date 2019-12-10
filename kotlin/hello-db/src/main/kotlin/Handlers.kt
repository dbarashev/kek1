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
  /* Почему EAGER? IDEA подсвечивает, что это поле вообще не используется. А загрузка много времени возьмет  */
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
    /* Для каждого полета, которых 100500 мы пилим запрос в базу? Эдак никакого пула не хватит
    * Это же все можно одним запросом выразить  */
    cacheFlights(flightDate).forEach { flightId ->
      withConnection(true) {
        updateCount += it.prepareStatement("UPDATE Flight SET date=date + interval '$interval' WHERE id=$flightId")
            .executeUpdate()
      }
    }
    return "Updated $updateCount flights"
  }


  fun handleDeletePlanet(planetId: Int) : String {
    /*
    * Почему hikari: false?
    * Если уж используем пул, разумно использовать везде
    *  */
    val deleteCount = withConnection(true) {
      it.prepareStatement("DELETE FROM Planet WHERE id=?").also { stmt ->
        stmt.setInt(1, planetId)
      }.executeUpdate()
    }
    /* Педантичность: удалилась либо одна, либо ноль -- странно выводить их количество, лучше уж флажок */
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
              /*
                Что происходит тот тут
                Мы извлекли полеты
                Их может быть очень много
                И для каждого из 100500 полетов снова пилим запрос в базу
                Она столько за всю жизнь не осилит :с
                И опять-таки, если пользователь запросил 100500 полетов, мы их все в кеш кладем?
                Так никакого кеша не хватит

                И опять таки, он же здесь нигде не инвалидируется
                Там может полетов таких уже давно нет

                Даже если вообще кеширование просто убрать, станет лучше
               */
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
