
Istio Gateway definition

```sh
$ kubectl apply -f - <<EOF
apiVersion: networking.istio.io/v1
kind: Gateway
metadata:
  name: mygateway
spec:
  selector:
    istio: ingressgateway # use istio default ingress gateway
  servers:
  - port:
      number: 443
      name: https
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: istio-ingress-certs
      minProtocolVersion: TLSV1_2
      maxProtocolVersion: TLSV1_3
      cipherSuites:
        # TLS 1.3 ciphers (automatic)
        - TLS_AES_128_GCM_SHA256
        - TLS_AES_256_GCM_SHA384
        - TLS_CHACHA20_POLY1305_SHA256
        # TLS 1.2 ciphers (RSA)
        - ECDHE-RSA-AES128-GCM-SHA256
        - ECDHE-RSA-AES256-GCM-SHA384
       # TLS 1.2 EC certificates
         - ECDHE-ECDSA-AES128-GCM-SHA256
        - ECDHE-ECDSA-AES256-GCM-SHA384
        - ECDHE-RSA-AES128-GCM-SHA256
        - ECDHE-RSA-AES256-GCM-SHA384
    hosts:
    - nginx.example.com
EOF
```

Kubernetes gateway style
```sh
$ cat <<EOF | kubectl apply -f -
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: mygateway
  namespace: istio-system
  annotations:
    networking.istio.io/tls-options: |
      minProtocolVersion: TLSV1_2
      maxProtocolVersion: TLSV1_3
      cipherSuites:
      - ECDHE-ECDSA-AES256-GCM-SHA384
      - ECDHE-RSA-AES256-GCM-SHA384
      - ECDHE-ECDSA-AES128-GCM-SHA256
      - ECDHE-RSA-AES128-GCM-SHA256
spec:
  gatewayClassName: istio
  listeners:
  - name: https
    hostname: "httpbin.example.com"
    port: 443
    protocol: HTTPS
    tls:
      mode: Terminate
      certificateRefs:
      - name: httpbin-credential
    allowedRoutes:
      namespaces:
        from: Selector
        selector:
          matchLabels:
            kubernetes.io/metadata.name: default
EOF
```
