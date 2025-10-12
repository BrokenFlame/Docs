Configure Istio Default Gateway to use NLB and allow egress

```sh
cat > override.yaml<<EOF
kind: Namespace
metadata:
  labels:
    kubernetes.io/metadata.name: istio-ingress
  name: istio-ingress
---
kind: Namespace
metadata:
  labels:
    kubernetes.io/metadata.name: istio-egress
  name: istio-egress
---
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: istio-control-plane
spec:
  profile: default
  components:
    ingressGateways:
    - name: istio-ingressgateway
      namespace: istio-ingress
      enabled: true
      labels:
        istio: ingressgateway
      k8s:
        serviceAnnotations:
          service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
          service.beta.kubernetes.io/aws-load-balancer-internal: "false"  # or "true" for internal
          service.beta.kubernetes.io/aws-load-balancer-security-groups: "sg-xxxxxxxx"
        service:
          type: LoadBalancer
      # Expose Prometheus metrics
      overlays: # delete this overlay section if prometheus is not installed.
      - apiVersion: v1
        kind: Service
        name: istio-ingressgateway
        patches:
        - path: spec.ports.[name: http-envoy-prom]
          value:
            name: http-envoy-prom
            port: 15090
            targetPort: 15090
            protocol: TCP
    egressGateways:
    - name: istio-egressgateway
      namespace: istio-egress
      enabled: true
      labels:
        istio: egressgateway
      overlays: # delete this overlay section if prometheus is not installed.
      - apiVersion: v1
        kind: Service
        name: istio-egressgateway
        patches:
        - path: spec.ports.[name: http-envoy-prom]
          value:
            name: http-envoy-prom
            port: 15090
            targetPort: 15090
            protocol: TCP
  meshConfig:
    enablePrometheusMerge: false  # Merge control-plane + sidecar metrics used for prometheus
    accessLogFile: /dev/stdout
    outboundTrafficPolicy:
      mode: ALLOW_ANY
    meshMTLS:
      minProtocolVersion: TLSV1_3
  values:
    gateways:
      istio-ingressgateway:
        injectionTemplate: gateway
    telemetry: # section can be deleted if prometheus is not installed
      v2:
        enabled: true
        prometheus:
          enabled: true
          serviceMonitor:
            enabled: true
            interval: 15s   # frequency for scraping metrics
  addonComponents:
      prometheus:
        enabled: false   # you will install Prometheus separately
      kiali:
        enabled: false    # optional; Kiali will need Prometheus access
      grafana:
        enabled: false
---
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: defaultPeerAuthentication
  namespace: default
spec:
  mtls:
    mode: PERMISSIVE  # STRICT or DISABLE
EOF
```

```sh
istioctl install --set profile=default  -f override.yaml
```


# Advanced Egress Gateway Rules
Below is only to get metrics and service mapping to work in Kiali or to force egress for common services via the egressgateway.

```sh
cat > egress-gateway.yaml<<EOF
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: egress-gateway
  namespace: istio-egress
spec:
  selector:
    istio: egressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "*"
  - port:
      number: 443
      name: https
      protocol: TLS
    hosts:
    - "*"
    tls:
      mode: PASSTHROUGH
  - port:
      number: 22
      name: ssh
      protocol: TCP
    hosts:
    - "*"
  - port:
      number: 21
      name: ftp
      protocol: TCP
    hosts:
    - "*"
  - port:
      number: 25
      name: smtp
      protocol: TCP
    hosts:
    - "*"
EOF
```

Catch all egress for HTTP and HTTPS
```sh
cat > egressRules.yaml<<EOF
apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: allow-all-external
spec:
  hosts:
  - "*"
  location: MESH_EXTERNAL
  ports:
  - number: 80
    name: http
    protocol: HTTP
  - number: 443
    name: https
    protocol: TLS
  resolution: NONE
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: redirect-external-through-egress
spec:
  hosts:
  - "*"
  gateways:
  - mesh  # Apply to internal traffic
  - istio-egressgateway  # Optional: allow routing at egress too
  tcp:
  - match:
    - port: 443
    route:
    - destination:
        host: istio-egressgateway.istio-egress.svc.cluster.local
        port:
          number: 443
  - match:
    - port: 80
    route:
    - destination:
        host: istio-egressgateway.istio-egress.svc.cluster.local
        port:
          number: 80
  - match:
    - port: 22   # SSH
    route:
    - destination:
        host: istio-egressgateway.istio-egress.svc.cluster.local
        port:
          number: 22
  - match:
    - port: 21   # FTP
    route:
    - destination:
        host: istio-egressgateway.istio-egress.svc.cluster.local
        port:
          number: 21
  - match:
    - port: 25   # SMTP
    route:
    - destination:
        host: istio-egressgateway.istio-egress.svc.cluster.local
        port:
          number: 25
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: egressgateway-for-external
spec:
  host: istio-egressgateway.istio-egress.svc.cluster.local
  trafficPolicy:
    tls:
      mode: PASSTHROUGH
EOF

kubectl apply -f egressRules.yaml
```
