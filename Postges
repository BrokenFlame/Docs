# Useful Postgres command (PSQL)

###Output results as CSV
```sql
\copy (SELECT * FROM <database_name>.<table>') To '/tmp/test.csv' With CSV DELIMITER ',' HEADER;
```

###Get table sizes
```sql
select 
  table_schema, 
  table_name,
  pg_relation_size('"'||table_schema||'"."'||table_name||'"')
from information_schema.tables
order by 3;
```

###Get Database size
```
\l+
```
or
```sql
SELECT pg_size_pretty(pg_database_size('Database Name'));
```

###List Databases
```
\l
```
or
```
SELECT * FROM pg_catalog.pg_tables;
```

###List Tables
```
dt
```

###Change Database
```sh
\c <database_name>
```

###Exit psq
```sh
\q 
```
