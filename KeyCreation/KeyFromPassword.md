# Generate Key from Password

OpenSSL provides the following function for deriving key from passwords:
- scrypt
- PBKDF2

__PBKDF2 is no longer recommended.__

```ssh
HEX_SALT=$(openssl rand -hex 16)
HEX_SALT > hex_salt.txt
```

example
```sh
openssl kdf -keylen 32 -kdfopt 'pass:$(PASSWORD)' -kdfopt hexsalt:$HEX_SALT -kdfopt -n:65536 -kdfopt r:8 -kdfopt p:1 SCRYPT 
```

Remember hex16 is 128 bit, hex32 is 256 bit.
