# OpenSSL Digital Signitures

## Select Eliptical Curve
OpenSSL will display a list of possuble Eliptical curves for the digital signiture, however it secp521r1 is recommended.
```sh
openssl ecparam -list_curves
```  

## Generate Key Pair
Generate a eliptical curve key pair, contained in a single file. 
```sh
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:<ec_curve> -out  <keypair.pem> 
```

## Extract Public Key
Extract the public key from the keypair file.
```sh
openssl pkey <keypair.pem> -pubout -out <publicKey.pem>
```
  
## Create digital signiture for file
Create a digital signiture using for the file using the command below.
```sh
openssl pkeyutl -sign -digest sha3-512 -inkey <keypair.pem> -in <filePath> -rawin -out <signatureFilePath>
```

## Signed file verification 
Check that the digital signiture is valid using the following command.  
```sh
openssl pkeyutl -verify -digest sha3-512 -inkey <publickey.pem> -in <filePath> -rawin -sigfile <signatureFilePath>
```
