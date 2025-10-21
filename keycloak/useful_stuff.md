# The init pod looks for a database host and port to be open but doesn't log update the Stateful Set if not using the Keycloak Operator:

```sh
sh -c '
echo "[dbchecker] Waiting for Database to become ready at keycloak.cyv7lv2wzbee.eu-west-2.rds.amazonaws.com:5432..."
while true; do
  TIMESTAMP=$(date +%Y-%m-%dT%H:%M:%S)
  if nc -z -w 2 <DB_HOST> <DB_Port>; then
    echo "[$TIMESTAMP] [dbchecker] Database is reachable!"
    break
  else
    echo "[$TIMESTAMP] [dbchecker] Database not reachable. Retrying in 2s..."
    sleep 2
  fi
done
'
```
