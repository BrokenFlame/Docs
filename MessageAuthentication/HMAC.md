# Hash Message Authentication Code
HMACs are useful for checking messages or file integrity where the key has been kept private.  For instance log messages written by a system to insecure storage can later be read back, along with the HMAC to confirm the integrity of the log messages. Due to the relatively low computational usage, HMAC are prefered in this senario over digital signatues.

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
```sh
HMAC=$(openssl rand -hex 32)
echo $HMAC > hmac_key.txt
```

## Create the Hash for the file/message
### Old command 
Create the message authentication code hash. •note that the output of the old command is in lowercase, so you may need to convert it to uppercase. To convert to upper case you can use the 'tr' command. 
```sh
openssl dgst -<hash_algorith> -mac HMAC -macopt hexkey:$HMAC <filename>
```

*example*
```sh
openssl dgst -sha-256 -mac HMAC -macopt hexkey:$HMAC <filename> | tr '[:lower:]' '[:upper:]'
```

### New Command
```sh
openssl mac -digest <hash_algorithm> -macopt hexkey:$HMAC -in <filename> HMAC
```
*example*
```sh
openssl mac -digest sha256 -macopt hexkey:$HMAC -in myfile.txt HMAC
```

## Create the Hash for a message
To create a HMAC for a text massage use the following command:
```sh
echo -n '<message>' | openssl mac -digest <hash_algorithm> -macopt hexkey:$HMAC -in - HMAC
```

*example*
```sh
echo -n 'Hello Kitty' | openssl mac -digest sha256 -macopt hexkey:$HMAC -in - HMAC
```
