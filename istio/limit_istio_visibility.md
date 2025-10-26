# Reduce Envoy visibility of other name spaces
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
