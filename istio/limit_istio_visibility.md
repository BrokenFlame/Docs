# Faster Envoy proxy

Reduce visibility to just what is required.
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: Sidecar
metadata:
  name: default
  namespace: <namespace>
spec:
  egress:
  - hosts:
    - "./*"     # same namespace
    - "istio-system/*"
```

Reduce visibility to just what is required, and set outbound traffic to Registered Services.
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: Sidecar
metadata:
  name: default
  namespace: orders
spec:
  egress:
  - hosts:
    - "./*"
    - "istio-system/*"
  outboundTrafficPolicy:
    mode: REGISTRY_ONLY
```
