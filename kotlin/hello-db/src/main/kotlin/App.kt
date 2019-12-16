// Copyright (C) 2019 Dmitry Barashev
package hellodb

import spark.Spark.*
import java.text.SimpleDateFormat
import java.util.*

class App() {
  private val handler = FlightsHandler()

  init {
    exception(Exception::class.java) { e, req, res ->
      e.printStackTrace()
    }
    staticFiles.location("/public")
    port(8080)

    get("/") { req, res ->
      "Hello DB"
    }
    get("/flights") { req, res ->
      res.header("Content-type", "text/html;charset=utf-8")
      val flightDate: Date? = req.queryParams("flight_date")?.let {
        SimpleDateFormat("yyyy-MM-dd").parse(it)
      }
      handler.handleFlights(flightDate)
    }
    get("/delay_flights") { req, res ->
      val flightDate: Date? = req.queryParams("flight_date")?.let {
        SimpleDateFormat("yyyy-MM-dd").parse(it)
      }
      val interval: String ? = req.queryParams("interval")
      if (flightDate == null || interval == null) {
        "Please specify flight_date and interval (in days) arguments, like this: /delay_flights?flight_date=2084-06-12&interval=7"
      } else {
        handler.handleDelayFlights(flightDate, interval.toInt())
      }
    }
    get("/delete_planet") { req, res ->
      val planetId: Int? = req.queryParams("planet_id")?.toIntOrNull()
      if (planetId == null) {
        "Please specify planet_id, like this: /delete_planet?planet_id=1"
      } else {
        handler.handleDeletePlanet(planetId)
      }
    }
  }

}

fun main(args: Array<String>) {
  App()
}
