# Generate Key from Password

OpenSSL provides the following function for deriving key from passwords:
- scrypt
- PBKDF2

__PBKDF2 is no longer recommended.__

## Generate the salt

```ssh
HEX_SALT=$(openssl rand -hex 16)
HEX_SALT > hex_salt.txt
```

# Generate the key

The following command is used to generate the key.
```sh
openssl kdf -keylen <keylength_in_hex> -kdfopt 'pass:<password>' -kdfopt hexsalt:<salt> -kdfopt -n:65536 -kdfopt r:8 -kdfopt p:1 <Algorithm> 
```

*example*
This example generates as 256bit key.

```sh
openssl kdf -keylen 32 -kdfopt 'pass:$(PASSWORD)' -kdfopt hexsalt:$HEX_SALT -kdfopt -n:65536 -kdfopt r:8 -kdfopt p:1 SCRYPT 
```

Remember hex16 is 128 bit, hex32 is 256 bit.
