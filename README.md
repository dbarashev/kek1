# test1

### SQL
по умолчанию пользователь postgres с пустым паролем на localhost:5432/postgres

```
psql -h localhost -U postgres -f sql/gen-schema.sql
psql -h localhost -U postgres -f sql/gen-data.sql
psql -h localhost -U postgres -c 'SELECT GenerateSchema(); SELECT GenerateData(1)'
```

### Python
```
cd python/hello-db
python3 app.py
```

### Kotlin
```
cd kotlin/hello-db
gradle run
```
