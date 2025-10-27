

```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: {{ .Release.Name }}-dr
spec:
  host: {{ printf "%s.%s.svc.cluster.local" .Release.Name .Release.Namespace | quote }}
  trafficPolicy:
    connectionPool:
      http:
        h2UpgradePolicy: UPGRADE          # enable HTTP/2 upgrade if client is HTTP/1
        maxRequests: 1024                  # max concurrent streams per HTTP/2 connection
      tcp:
        maxConnections: 10                 # max TCP connections to each pod
    outlierDetection:
      consecutive5xxErrors: 5              # optional: eject unhealthy pods automatically
      interval: 10s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
    # Idle timeout closes idle connections to free resources and improve LB efficiency
    idleTimeout: 30s

  ```
