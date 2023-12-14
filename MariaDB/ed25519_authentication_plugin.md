# Enable ed25519 authentication plugin
This plug in is used to securle store user passwords.

To use it you must use a modified version of the create user and grant commands
```sql
CREATE USER username@hostname IDENTIFIED VIA ed25519 USING PASSWORD('secret');
GRANT SELECT ON db.* TO username@hostname IDENTIFIED VIA ed25519 USING PASSWORD('secret');
```

### Get the location of the options file
```sh 
mariadbd --help --verbose
```

### Configure the plugin
```sh
[mariadb]
...
plugin_load_add = auth_ed25519
```

### Disable old password
Disable the old password manager
```sh
[mariadb]
...
old_passwords=0
```

## Verification

```sh
SHOW VARIABLES WHERE Variable_name = 'old_passwords';
```
