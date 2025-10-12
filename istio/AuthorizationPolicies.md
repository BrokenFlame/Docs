# Application and Namespace protection


# Generic deny all.
The following will prevent communication from other namespaces to the namespace specified as well as in namespace communications.
```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: deny-all
  namespace: default
spec: {}
```

# Once the deny AuthorizationPolicy has been applied then grant access to the namespaces that need to talk to your namespace:
```sh
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-from-trusted
  namespace: default
spec:
  # default action is ALLOW when rules exist
  rules:
  - from:
    # allow calls from same namespace (intra-app)
    - source:
        namespaces: ["default"]
  - from:
    # allow calls from istio ingress (e.g. istio-system)
    - source:
        namespaces: ["istio-system", "istio-ingress"]
  - from:
    # allow calls from specific cluster service namespaces if they must call the app
    - source:
        namespaces: ["kube-system", "prometheus","cert-manager", "external-dns"]
```

## Allowing specific application access
If you want to allow access from App1 to App2 use the service account on App 1 as the identifier. 
```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-app1-to-app2
  namespace: app-a
spec:
  selector:
    matchLabels:
      app: app2    # this protects only app2’s pods
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/app-a/sa/app1-sa"]
```
