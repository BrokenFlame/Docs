# Keycloak Install


## Install the CRDs
```sh
kubectl apply -f https://raw.githubusercontent.com/keycloak/keycloak-k8s-resources/26.4.1/kubernetes/keycloaks.k8s.keycloak.org-v1.yml
kubectl apply -f https://raw.githubusercontent.com/keycloak/keycloak-k8s-resources/26.4.1/kubernetes/keycloakrealmimports.k8s.keycloak.org-v1.yml
```

## Install the Operator
```sh
kubectl create namespace keycloak
kubectl -n keycloak apply -f https://raw.githubusercontent.com/keycloak/keycloak-k8s-resources/26.4.1/kubernetes/kubernetes.yml
```

## Reconfigure the operator watcher if not installing into the keycloak namespace. Not the operator watches keycloak in its own namespace
```sh
# Replace custom-namespace with the namespace name. 
kubectl -n custom-namespace apply -f https://raw.githubusercontent.com/keycloak/keycloak-k8s-resources/26.4.1/kubernetes/kubernetes.yml
kubectl patch clusterrolebinding keycloak-operator-clusterrole-binding --type='json' -p='[{"op": "replace", "path": "/subjects/0/namespace", "value":"custom-namespace"}]'
# restart the operator
kubectl rollout restart -n custom-namespace Deployment/keycloak-operator
```


## Operator Configuration


Allow cache between keycloak nodes
```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: infinispan-allow-nomtls
  namespace: keycloak
spec:
  selector:
    matchLabels:
      app: keycloak 
  portLevelMtls:
    "7800": 
      mode: PERMISSIVE
```

Allow the infinispace failure detection port

```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: infinispan-allow-nomtls-offset
spec:
  selector:
    matchLabels:
      app: keycloak 
  portLevelMtls:
    "57800": 
      mode: PERMISSIVE
```

Create database secret for username and password:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: kc-db-creds
type: Opaque
data:
  username: YWRtaW4=       # base64 encoded 'admin'
  password: UzNjcjN0U0Bzcy= # base64 encoded 'S3cr3tP@ss'
```


```yaml
apiVersion: k8s.keycloak.org/v2alpha1
kind: Keycloak
metadata:
  name: keycloak
spec:
  instances: 2   # Number of Keycloak pods / replicas
  db:
    vendor: postgres
    usernameSecret:
      name: kc-db-creds
      key: username
    passwordSecret:
      name: kc-db-creds
      key: password
    host: host
    database: database
    port: 5432
    schema: public # default schema
    poolInitialSize: 10
    poolMinSize: 10
    poolMaxSize: 50
  http:
    httpEnabled: true # Allow HTTP connections
    httpPort: 8080
    # httpsPort: 443
    # tlsSecret: my-tls-secret
    labels: {}
    annotations: {}
  proxy: edge
  proxy:
    headers: forwarded
  hostname:
    hostname: https://my-hostname.tld
    admin: https://my-hostname.tld/admin
    strict: true # Force the use of correct hostnames (should be true in production)
    backchannelDynamic: false
  features:
    enabled:
      - authorization
      - admin
    disabled:
      - docker
      - step-up-authentication
  transaction:
    xaEnabled: false
  readinessProbe:
    periodSeconds: 20
    failureThreshold: 5
  livenessProbe:
    periodSeconds: 20
    failureThreshold: 5
  startupProbe:
    periodSeconds: 20
    failureThreshold: 5
  tracing:
    enabled: false                            # default 'false'
  serviceMonitor:
    enabled: false
  additionalOptions:
    - name: log-level
      value: INFO
    - name: quarkus.http.proxy.proxy-address-forwarding
      value: "true"

```

Create Keycloak Realm
```yaml
apiVersion: keycloak.org/v1alpha1
kind: KeycloakRealm
metadata:
  name: kc-general-realm
spec:
  realm:
    id: general
    realm: general
    displayName: General
    enabled: true
  keycloakCRName: my-keycloak
```


# Ingress
The official Keycloak operator using ClusterIP for services. In AWS means creating an Ingress manually via istio or ALB controller:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: keycloak-ingress
  namespace: keycloak
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP":80}, {"HTTPS":443}]'
    alb.ingress.kubernetes.io/certificate-arn: arn:aws:acm:region:account:certificate/your-certificate-id
    alb.ingress.kubernetes.io/ssl-redirect: '443'
    alb.ingress.kubernetes.io/target-type: ip
spec:
  rules:
  - host: keycloak.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: keycloak-service    # The service created by operator
            port:
              number: 8080            # Service port exposed by Keycloak
```
