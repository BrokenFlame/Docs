# Key Usage Rules

## CA ONLY

***keyCertSign***
Subject public key is used to verify signatures on certificates
This extension must only be used for CA certificates
cRLSign

Subject public key is to verify signatures on revocation information, such as a CRL
This extension must only be used for CA certificates

***digitalSignature***
Certificate may be used to apply a digital signature
Digital signatures are often used for entity authentication & data origin authentication with integrity
nonRepudiation

Certificate may be used to sign data as above but the certificate public key may be used to provide non-repudiation services
This prevents the signing entity from falsely denying some action
keyEncipherment

----

## Generic KeyUsage

Certificate may be used to encrypt a symmetric key which is then transferred to the target
Target decrypts key, subsequently using it to encrypt & decrypt data between the entities
dataEncipherment

Certificate may be used to encrypt & decrypt actual application data
keyAgreement

Certificate enables use of a key agreement protocol to establish a symmetric key with a target
Symmetric key may then be used to encrypt & decrypt data sent between the entities
encipherOnly

Public key used only for enciphering data while performing key agreement
Req. KU: keyAgreement
decipherOnly

Public key used only for deciphering data while performing key agreement
***Req. KU***: keyAgreement


## extendedKeyUsage
CAs/ICAs should not have any EKUs specified

**serverAuth**
All VPN/Web servers should be signed with this EKU present
(this supersedes nscertype options, as ns in nscertype stands for NetScape [browser])
SSL/TLS VPN/Web Server authentication EKU, distinguishing a server which clients can authenticate against
Req. KU: digitalSignature, keyEncipherment or keyAgreement
clientAuth

All VPN clients must be signed with this EKU present
SSL/TLS Web/VPN Client authentication EKU distinguishing a client as a client only
Req. KU: digitalSignature and/or keyAgreement
codeSigning

**Code Signing**
***Req. KU***: digitalSignature, nonRepudiation, and/or keyEncipherment or keyAgreement
emailProtection

Email Protection via S/MIME, allows you to send and receive encrypted emails
Req. KU: digitalSignature, keyEncipherment or keyAgreement
timeStamping

**Trusted Timestamping**
***Req. KU***: digitalSignature, nonRepudiation
OCSPSigning

**OCSP Signing**
***Req. KU***: digitalSignature, nonRepudiation
msCodeInd

**Microsoft Individual Code Signing (authenticode)**
***Req. KU***: digitalSignature, keyEncipherment or keyAgreement
msCodeCom

**Microsoft Commerical Code Signing (authenticode)**
***Req. KU***: digitalSignature, keyEncipherment or keyAgreement
mcCTLSign

**Microsoft Trust List Signing**
***Req. KU***: digitalSignature, nonRepudiation
msEFS

**Microsoft Encrypted File System Signing**
***Req. KU***: digitalSignature, keyEncipherment or keyAgreement

## Examples

### Self-signed CA

**keyUsage**: cRLSign, digitalSignature, keyCertSign
***(Should not contain any other KUs and no EKUs)***
V3 Profile:

```sh
[ v3_ca ]
basicConstraints        = critical, CA:TRUE
subjectKeyIdentifier    = hash
authorityKeyIdentifier  = keyid:always, issuer:always
keyUsage                = critical, cRLSign, digitalSignature, keyCertSign
subjectAltName          = @alt_ca
```

### Intermediate CA
**keyUsage**: cRLSign, digitalSignature, keyCertSign
***(Should not contain any other KUs and no EKUs)***

```sh
V3 Profile:
[ v3_ica ]
basicConstraints        = critical, CA:TRUE, pathlen:0
subjectKeyIdentifier    = hash
authorityKeyIdentifier  = keyid:always, issuer:always
keyUsage                = critical, cRLSign, digitalSignature, keyCertSign
subjectAltName          = @alt_ica
```

Where pathlen: is equal to the number of CAs/ICAs it can sign
***(if pathlen is not specified/number set, it can sign an infinite/specified number of CAs/ICAs)***

### Non-CA Certificates

#### VPN/Web Server
**keyUsage**: nonRepudiation, digitalSignature, keyEncipherment, keyAgreement
V3 Profile:

```sh
[ v3_vpn_server ]
basicConstraints        = critical, CA:FALSE
subjectKeyIdentifier    = hash
authorityKeyIdentifier  = keyid:always, issuer:always
keyUsage                = critical, nonRepudiation, digitalSignature, keyEncipherment, keyAgreement 
extendedKeyUsage        = critical, serverAuth
subjectAltName          = @alt_vpn_server
```

#### VPN Client
**keyUsage**: nonRepudiation, digitalSignature, keyEncipherment
V3 Profile:

```sh
[ v3_vpn_client ]
basicConstraints        = critical, CA:FALSE
subjectKeyIdentifier    = hash
authorityKeyIdentifier  = keyid:always, issuer:always
keyUsage                = critical, nonRepudiation, digitalSignature, keyEncipherment
extendedKeyUsage        = critical, clientAuth
subjectAltName          = @alt_vpn_client
```
## Additional Notes
**Critical** flag specifies whether the information in an extension is important. If an application doesn't recognize the extension marked as "**critical**", the certificate cannot be accepted. If an extension is not marked as critical (critical value False) it can be ignored by an application.

In Windows, critical extensions are marked with a yellow exclamation mark in the certificates property dialog.
