
Display hosted certificate details

```sh
echo | openssl s_client -connect <fqdn>:<port> -showcerts
```

Read server certificate for SNI
```
openssl s_client -showcerts -servername <SNI>  -connect <Server Address>:443 </dev/null
```

Open mTLS connect with client certificate

```sh
openssl s_client -connect <fqdn>:<port> -CAFile <CACert>.pem -key <Client_Cert_Key>.pem -cert <Client_Cert>.pem
```

```sh
openssl s_client -connect <fqdn>:<port> -chainCAfile <CAChainCert>.pem -key <Client_Cert_Key>.pem -cert <Client_Cert>.pem
```

Create RSA Private Key
```sh
openssl genpkey -algorithm rsa -pkeyopt rsa_keygen_bits:2048
```

Generic Config file:
```sh
[req]
default_bits        = 2048
prompt              = no
default_md          = SHA256
distinguished_name  = distinguished_name_client_cert
req_extensions      = req_ext

[distinguished_name_client_cert]
countryName         = GB
stateOrProvinceName = London
localityName        = London
organizationName    = Company Name
commonName          = www.mycompany.com
emailAddress        = me@mycompany.com

[req_ext]
basicConstraints    = CA:FALSE
keyUsage            = critical, nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage    = critical, serverAuth, clientAuth
```

Create CSR from config
```sh
openssl req -new -config <configFile> -key <privateKey> -out servers.csr
```

Verify CSR content
```sh
openssl req -in <csrFile> -noout -text
```

Convert CER to PFX (PKCS12)
```sh
openssl pkcs12 -export -in ServerCertificate.crt -certfile CABundle.crt -inkey private-key.pem -out certificate.pfx
```

Get Certificate Fingerprint
```sh
openssl x509 -noout -fingerprint -sha256 -inform pem -in ServerCertificate.crt 
```
or 
```sh
openssl x509 -noout -fingerprint -sha1 -inform pem -in ServerCertificate.crt 
```

Get PFX cert information
```sh
openssl pkcs12 -in example.pfx -passin pass:your_password -info
```

Get start and end date for certificate on live server
```sh
openssl s_client -servername <FQDN> -connect <FQDN>:<port> | openssl x509 -noout -dates
```

Get end date for certificate on live server
```sh
openssl s_client -servername <FQDN> -connect <FQDN>:<port> | openssl x509 -noout -enddate
```

Check is SSL Certificate will expire in 1 day. Adjust TIMEINSECONDS from now to check if the certificate will expire within the duration. 1 day is equal to 86400 seconds. 2 Weeks is equal to 1209600 seconds.
```sh
openssl s_client -showcerts -connect <FQND>:443 -servername <FQND> </dev/null 2>/dev/null |openssl x509 -checkend <TIMEINSECONDS> 
```

Decrypt RSA Private Key
```sh
openssl rsa -in encrypted_PrivateKey.pem -out PrivateKey.pem
```
