# GZip Compression for APIs and HTML on the Istio ingress

Apply in the namespace of the ingress, also remeber to update the label selector.

```yaml
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: gateway-gzip-compression
  namespace: istio-system
spec:
  workloadSelector:
    labels:
      istio: ingressgateway
  configPatches:
  - applyTo: HTTP_FILTER
    match:
      context: GATEWAY
      listener:
        filterChain:
          filter:
            name: envoy.filters.network.http_connection_manager
            subFilter:
              name: envoy.filters.http.router
    patch:
      operation: INSERT_BEFORE
      value:
        name: envoy.filters.http.compressor
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.filters.http.compressor.v3.Compressor
          response_direction_config:
            common_config:
              min_content_length: 256
              content_type:
                - application/json
                - application/xml
                - text/html
                - application/javascript
          compressor_library:
            name: text_optimized
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.compression.gzip.compressor.v3.Gzip
              memory_level: 9
              compression_level: BEST_COMPRESSION
```

Set the compression and memory as required:

| Compression Level    | Memory Level | Compression Ratio | Example: 2,580 KB → | Speed   | CPU Usage           |
  |----------------------|--------------|-------------------|---------------------|---------|---------------------|
  | 1 (BEST_SPEED)       | 1-3          | 60-65%            | 900-1,032 KB        | Fastest | Low (+5-10%)        |
  | 4-5                  | 4-5          | 70-72%            | 722-774 KB          | Fast    | Medium (+12-15%)    |
  | 6 (DEFAULT)          | 5-6          | 75-78%            | 567-645 KB          | Medium  | Medium (+15-20%)    |
  | 7-8                  | 7-8          | 78-82%            | 464-567 KB          | Slow    | High (+30-40%)      |
  | 9 (BEST_COMPRESSION) | 9            | 80-85%            | 387-516 KB          | Slowest | Very High (+40-60%) |
