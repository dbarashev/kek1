package hellodb

import com.zaxxer.hikari.HikariDataSource
import java.sql.Connection
import java.sql.DriverManager


lateinit var url: String
lateinit var dataSource: HikariDataSource

fun initDb(user: String = "postgres", password: String = "12345", database: String = "postgres") {
  url = "jdbc:postgresql://localhost/$database?user=$user&defaultAutoCommit=false&password=$password"
  dataSource = HikariDataSource().apply {
    username = user
    jdbcUrl = "jdbc:postgresql://localhost:5432/$database"
    this.password = password
    maximumPoolSize = 10
  }
}

fun <T> withConnection(code: (Connection) -> T) : T {
  return dataSource.connection.use(code)
}
