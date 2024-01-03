# Revoke Certificate

1. To revoke a certificate use the following command:

```sh
openssl ca -config <CAConfigFile.cfg> -revoke <certToRevoke.pem> -crl_reason [ keyCompromise | affiliationChanged | superseded | cessationOfOperation | privilegeWithdrawn]

```

** Remember to generate the certificate revocation list crl and publish it after revoking a certificate **
