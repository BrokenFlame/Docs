# MariaDB Encryption at Rest Configuration

## File Key Management Encryption Plugin

### Generate encryption keys
Only one key is required, but multiple should be created.

```sh
$(echo -n "1;" ; openssl rand -hex 32 ) | sudo tee -a  /etc/mysql/encryption/keyfile
$(echo -n "2;" ; openssl rand -hex 32 ) | sudo tee -a  /etc/mysql/encryption/keyfile
$(echo -n "3;" ; openssl rand -hex 32 ) | sudo tee -a  /etc/mysql/encryption/keyfile
```

### Encrypt the encryption key file
Generate a key to preform the encryption with:
```sh
openssl rand -hex 128 > /etc/mysql/encryption/keyfile.key
```
Then encrypt the file
```sh
openssl enc -aes-256-cbc -md sha1 -pass file:/etc/mysql/encryption/keyfile.key -in /etc/mysql/encryption/keyfile -out /etc/mysql/encryption/keyfile.enc
rm /etc/mysql/encryption/keyfile.key
```

### Get the location of the options file
```sh 
mariadbd --help --verbose
```

### Configure the plugin
```sh
[mariadb]
...
plugin_load_add = file_key_management
loose_file_key_management_filename = /etc/mysql/encryption/keyfile.enc
loose_file_key_management_filekey = FILE:/etc/mysql/encryption/keyfile.key
```

### Start the server
Start the server
```sh

```

## Verification
Verify that the plugin is loaded by connecting to the server and executing the following command:

```sql
SELECT * FROM information_schema.PLUGINS\G
```
