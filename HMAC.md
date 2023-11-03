# Hash Message Authentication Code

## Select a hashing algorithm 
Use the following command to list the hashing algorithms available.  It is recommended that you use sha256
```sh
openssl list -digest-commands
```

## Generate a Random Key
Create a random key for the Message Authentication Hash function.  This will be the preshared-key for creating the hash and message authentication code later.

```sh
HMAC=$(openssl rand -hex 32)
echo $HMAC > <hash_filename>
```

*example*
HMAC=$(openssl rand -hex 32)
echo $HMAC > hmac_key.txt

## Create the Hash for the file/message
### Old command
Create the message authentication code hash.
```sh
openssl dgst -sha-256 -mac HMAC -macopt hexkey:$HMAC <filename>
```

### New Command
```sh
openssl mac -digest sha256 -macopt hexkey:$HMAC -in <filename> HMAC
```
*example*
```sh
openssl mac -digest sha256 -macopt hexkey:$HMAC -in myfile.txt HMAC
```

## Create the Hash for a message
To create a HMAC for a text massage use the following command:
```sh
echo -n '<message>' | openssl mac -digest SHA-256 -macopt hexkey:$HMAC -in - HMAC
```

*example*
```sh
echo -n 'Hello Kitty' | openssl mac -digest SHA-256 -macopt hexkey:$HMAC -in - HMAC
```
