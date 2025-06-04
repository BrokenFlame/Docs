# Encrypt and Decrypt via GPG CLI

## Encrypt a file using the recipient key in a file 

```
gpg --encrypt --recipient-file [Recipient Public GPG Key] --output [OUT_FILE] [FILE]
```
Example
```sh
gpg --encrypt --recipient-file recipient.gpg.pub --output message.gpg message.txt
```

## Encrypt a sting using the recipient public key in a file
Note if you are sending encrypted string via email or over the web it is recommended to base64 encode the output of the PGP encryption.

```sh
echo -n "Sample Text" | gpg --encrypt --armor --recipient-file [Recipient GPG Public Key]
```

Example
```sh
echo -n "My Message" | gpg --encrypt --armor --recipient-file recipient.gpg.pub
```



** Note --recipient-file is not listed in the gpg help ** 
