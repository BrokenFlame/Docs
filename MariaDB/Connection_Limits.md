# Set Maximum Connection Limits for Server and per User

```sql
SET GLOBAL max_user_connections=<desired numeric value>;
```

## Verification
Check the Global settings for the connection limits
```sql
SELECT VARIABLE_NAME, VARIABLE_VALUE FROM information_schema.global_variables WHERE VARIABLE_NAME LIKE 'max_%connections';
```


## Set per user connection limits
Set the per user connection limits for the maxium number of concurrent connections.
```sql
ALTER USER 'fred'@'%'
WITH MAX_CONNECTIONS_PER_HOUR 12
MAX_USER_CONNECTIONS 5;
```

## Verification
Verify the number max user connection per user.
```sql
select user, host, max_connections, max_user_connections from mysql.user
where user not like 'mysql.%' and user not like 'root';
```
