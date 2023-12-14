# MariaDB User Authentication

## Configure the server to use the SSL Certificates
Update the options file to include the path to the Server Key pair and Certificate Authorities public certificate, and set the TLS versions.

```sh
[mariadb]
...
ssl_cert = /etc/my.cnf.d/certificates/server-cert.pem
ssl_key = /etc/my.cnf.d/certificates/server-key.pem
ssl_ca = /etc/my.cnf.d/certificates/ca.pem
tls_version = TLSv1.2,TLSv1.3
ssl_cipher='ECDHE-ECDSA-AES128-GCM-SHA256'
```

## Verify Server Configuration
Check that server is using OpenSSL
```sql
SHOW GLOBAL VARIABLES LIKE 'have_openssl';
```

Check OpenSSL version being utilised by server
```sql
SHOW GLOBAL VARIABLES LIKE 'version_ssl_library';
```

Check the dynamic link between MariaDB and the OpenSSL SO file
```sh
ldd $(which mysqld) | grep -E '(libssl|libcrypto)'
```


## User Configuration

### Update existing users
Use the Alter User command to update exiting users so that their connections require X509 authentication.
```sql
ALTER USER 'alice'@'%' 
   REQUIRE X509;
```
Determine a strong cipher suite that is FIPS compliant for the user to use, and ensure that they are required to connect using the appriopriate cipher suite.  

```sql
ALTER USER 'alice'@'%' 
   REQUIRE CIPHER 'ECDH-RSA-AES256-SHA384';
```
Then assoicate a subject line with the users from their certificate. 
```sql
ALTER USER 'alice'@'%' 
   REQUIRE SUBJECT '/CN=alice/O=My Dom, Inc./C=US/ST=Oregon/L=Portland';
```
Ideally the issuer should also be added for stronger authentication, but this is not required.
```sql

ALTER USER 'alice'@'%' 
   REQUIRE SUBJECT '/CN=alice/O=My Dom, Inc./C=US/ST=Oregon/L=Portland'
   AND ISSUER '/C=FI/ST=Somewhere/L=City/ O=Some Company/CN=Peter Parker/emailAddress=p.parker@marvel.com';
```

### New users
If a new user should have access from the local host create a localhost user as normal, and then the remote user.
```sql
CREATE USER 'alice'@'localhost' 
   REQUIRE NONE;

CREATE USER 'alice'@'%'
   REQUIRE SUBJECT '/CN=alice/O=My Dom, Inc./C=US/ST=Oregon/L=Portland'
   AND ISSUER '/C=FI/ST=Somewhere/L=City/ O=Some Company/CN=Peter Parker/emailAddress=p.parker@marvel.com'
   AND CIPHER 'ECDHE-ECDSA-AES256-SHA384';
```

Otherwise simply create the remote user with the approiate cipher suite and approiate certificate subject line.
```sql
CREATE USER 'alice'@'%'
   REQUIRE SUBJECT '/CN=alice/O=My Dom, Inc./C=US/ST=Oregon/L=Portland'
   AND ISSUER '/C=FI/ST=Somewhere/L=City/ O=Some Company/CN=Peter Parker/emailAddress=p.parker@marvel.com'
   AND CIPHER 'ECDHE-ECDSA-AES256-SHA384';
```

## Verification
To verify that a session is encrypted execute the following command:

```sql 
SELECT VARIABLE_NAME, VARIABLE_VALUE
FROM information_schema.global_variables
WHERE VARIABLE_NAME = 'ssl_cipher';
```
Current session
```sql
SHOW SESSION STATUS LIKE 'ssl_cipher';
```
