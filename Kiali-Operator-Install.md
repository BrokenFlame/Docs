Install Kiali for Google using Istio Ingress:

```sh
apiVersion: networking.istio.io/v1
kind: Gateway
metadata:
  name: kiali-gateway
  namespace: istio-system
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 443
      name: https-kiali
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: kiali-tls
    hosts:
    - "kiali.mycompany.com"
---
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: kiali-vs
  namespace: istio-system
spec:
  gateways:
  - kiali-gateway
  hosts:
  - "kiali.mycompany.com"
  http:
  - headers:
      request:
        set:
          X-Forwarded-Port: "443"
    route:
     - destination:
         host: kiali
         port:
           number: 20001
---
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: kiali
  namespace: istio-system
spec:
  host: kiali
  trafficPolicy:
    tls:
      mode: DISABLE
---
apiVersion: v1
kind: Secret
metadata:
  name: kiali
  namespace: istio-system
  labels:
    app: kiali
type: Opaque
data:
  oidc-secret: <OIDC Secret>
EOF
```

Create file for Helm Values called helm-values-kiali-operator.yaml
```txt
cr:
  create: true
  namespace: istio-system
  spec:
    auth:
      strategy: "openid"
      openid:
        client_id: "********************.apps.googleusercontent.com"
        disable_rbac: true
        issuer_uri: "https://accounts.google.com"
        scopes: ["openid", "email"]
        username_claim: "email"
```

Apply Kiali Secret for OIDC, and then run helm
```sh
kubectl apply -f kiali-secret.yaml
helm repo add kiali https://kiali.org/helm-charts
helm repo update
helm install -f helm-values-kiali-operator.yaml --namespace kiali-operator --create-namespace kiali-operator  kiali/kiali-operator
```

