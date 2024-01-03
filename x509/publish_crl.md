# Generate the Certificate Revocation List (CRL)

To generate the crl provide the CA config file for the CA you are publishing the CRL for, along with filename you want to use for the crl file. You should find the appropriate file name for the crl file in the CA configuration file or certificate issued by this CA.

Typically you should run the following commands from with the directory where your CA configuration file is held.

1. To generate the CRL file execute the following command:

```sh
openssl ca -config <CAConfig.cfg> -gencrl -out crl.pem
```

2. Verify the contents of the CRL PEM file.

```sh
openssl crl -in crl.pem -noout -text
```

3. Usually CRLs are hosted as DER files, to convert the file from PEM to DER execute the following command.

```sh
openssl crl -in crl.pem -outform DER -out crl.der
```

4. Verify the contents of the CRL DER file.

```sh
openssl crl -in crl.der -text -noout
```

5. Remeber to rename the published file to match the CRL file name in the Certificate
