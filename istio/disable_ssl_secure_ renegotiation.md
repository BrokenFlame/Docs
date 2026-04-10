# Disable TLS Secure Renegotiation on Ingress Gateway

```yaml
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: disable-renegotiation
  namespace: istio-ingress
spec:
  workloadSelector:
    labels:
      istio: ingressgateway
  configPatches:
    - applyTo: FILTER_CHAIN
      match:
        listener:
          filterChain:
            tlsContext:
              commonTlsContext: {}
      patch:
        operation: MERGE
        value:
          transport_socket:
            name: envoy.transport_sockets.tls
            typed_config:
              "@type": ://googleapis.com
              common_tls_context:
                tls_params:
                  # Disables client-initiated renegotiation
                  renegotiation_allowed: false
```
