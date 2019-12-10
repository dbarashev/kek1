package hellodb

import com.zaxxer.hikari.HikariDataSource
import java.sql.Connection
import java.sql.DriverManager


lateinit var url: String
lateinit var dataSource: HikariDataSource

fun initDb(user: String = "postgres", password: String = "", database: String = "postgres") {
  url = "jdbc:postgresql://localhost/$database?user=$user&defaultAutoCommit=false&password=$password"
  dataSource = HikariDataSource().apply {
    username = user
    jdbcUrl = "jdbc:postgresql://localhost:5432/$database"
    this.password = password
    maximumPoolSize = 10
  }
}

fun <T> withConnection(hikari: Boolean, code: (Connection) -> T) : T {
  return if (hikari) dataSource.connection.use(code) else code(getconn())
}

fun getconn(): Connection {
  return DriverManager.getConnection(url).also {
    it.autoCommit = false
  }
}
