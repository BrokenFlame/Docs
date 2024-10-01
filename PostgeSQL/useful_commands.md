# Useful Postgres command (PSQL)

### Output results as CSV
```sql
\copy (SELECT * FROM <database_name>.<table>') To '/tmp/test.csv' With CSV DELIMITER ',' HEADER;
```

### Get table sizes
```sql
select 
  table_schema, 
  table_name,
  pg_relation_size('"'||table_schema||'"."'||table_name||'"')
from information_schema.tables
order by 3;
```
### Get specific table size
```sql
SELECT pg_size_pretty(pg_relation_size('table_name'));
```

### Get Database size
```sql
\l+
```
or
```sql
SELECT pg_size_pretty(pg_database_size('Database Name'));
```

### List Databases
```sql
\l
```
or
```sql
SELECT * FROM pg_catalog.pg_tables;
```

### List Tables
```sql
\dt
```

### Change Database
```sh
\c <database_name>
```

### Exit psql
```sh
\q 
```
