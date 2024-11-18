
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

Create CSR from config
```sh
openssl req -new -config <configFile> -key <privateKey> -out servers.csr
```
