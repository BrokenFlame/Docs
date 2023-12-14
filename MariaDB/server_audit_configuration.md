# MariaDB Audits plugin configuration

### Get the location of the plugin director
```sql
SHOW GLOBAL VARIABLES LIKE 'plugin_dir';
```

### Ensure the plugin is available.
Ensure the so or dll file server_audit is in the plugin directory

### Get the location of the options file
```sh 
mariadbd --help --verbose
```

### Configure the plugin
```sh
[mariadb]
...
plugin_load_add = server_audit
server_audit=FORCE_PLUS_PERMANENT
server_audit_events = 'CONNECT, QUERY, TABLE, QUERY_DDL, QUERY_DML, QUERY_DCL, QUERY_DML_NO_SELECT'
server_audit_output_type = SYSLOG
```
### Verify that the plugin has loaded
Connect to the server and execute the following command
```sql
SHOW GLOBAL VARIABLES LIKE 'server_audit%';
```

# Get the plugin status
Connect to the server and execute:
```sh
SHOW STATUS LIKE 'server_audit%';
```
