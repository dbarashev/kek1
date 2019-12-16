package hellodb

import java.math.BigDecimal
import java.time.LocalDate
import java.util.*
import javax.persistence.*
import javax.persistence.criteria.CriteriaQuery
import javax.persistence.criteria.Fetch
import javax.persistence.criteria.Root


@Entity(name = "planet")
open class PlanetEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    val id: Int? = null
    var name: String? = null
    var distance: BigDecimal? = null
}

@Entity(name = "flight")
open class FlightEntity {
    @Id
    var id: Int? = null
    var date: Date? = null
    @ManyToOne
    @JoinColumn(name = "planet_id")
    var planet: PlanetEntity? = null
}

@Suppress("JpaQlInspection")
class FlightsHandler() {
    private val emf = Persistence.createEntityManagerFactory("Postgres")

    fun handleFlights(flightDate: Date?): String {
        val tablebody = withinTransaction {
            getFlights(flightDate, it)
        }!!.map {
            """<tr><td>${it.id}</td><td>${it.date}</td><td>${it.planet?.name}</td><td>${it.planet?.id}</td></tr>"""
        }.joinToString(separator = "\n")
        return "$FLIGHTS_HEADER $tablebody $FLIGHTS_FOOTER"
    }

    private fun getFlights(flightDate: Date?, entityManager: EntityManager): List<FlightEntity> {
        val cb = entityManager.criteriaBuilder
        val flightCriteria: CriteriaQuery<FlightEntity> = cb.createQuery(FlightEntity::class.java)
        val flightRoot: Root<FlightEntity> = flightCriteria.from(FlightEntity::class.java)
        @Suppress("UNUSED_VARIABLE") val fetch: Fetch<FlightEntity, PlanetEntity> = flightRoot.fetch("planet")
        flightCriteria.select(flightRoot)

        if (flightDate != null) {
            val dateProperty = flightRoot.get<LocalDate>("date")
            flightCriteria.where(cb.equal(dateProperty, flightDate))
        }
        return entityManager.createQuery(flightCriteria).resultList
    }

    fun handleDelayFlights(flightDate: Date, interval: Int): String {
        val c = Calendar.getInstance()
        c.time = flightDate
        c.add(Calendar.DAY_OF_MONTH, interval)
        val updateCount = withinTransaction {
            it.createQuery("UPDATE flight f SET f.date=:newDate WHERE f.date=:initDate")
                    .setParameter("initDate", flightDate)
                    .setParameter("newDate", c.time)
                    .executeUpdate()
        }!!

        return "Updated $updateCount flights"
    }

    fun handleDeletePlanet(planetId: Int): String {
        return withinTransaction {
            val entityCount = it.createQuery("DELETE FROM planet p WHERE p.id = :id")
                    .setParameter("id", planetId)
                    .executeUpdate()
            "Deleted $entityCount planets"
        }!!
    }

    private fun <T> withinTransaction(code: (EntityManager) -> T?): T? {
        val entityManager = emf.createEntityManager()
        val tx = entityManager.transaction
        tx.begin()
        try {
            return code(entityManager)?.also { tx.commit() }
        } catch (e: Exception) {
            tx.rollback()
            throw RuntimeException(e)
        } finally {
            entityManager.close()
        }
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
