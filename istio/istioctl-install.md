Configure Istio Default Gateway to use NLB and allow egress

```sh
cat > override.yaml<<EOF
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
      label:
        istio: ingressgateway
      k8s:
        serviceAnnotations:
          service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
          service.beta.kubernetes.io/aws-load-balancer-internal: "false"  # or "true" for internal
        service:
          type: LoadBalancer
    egressGateways:
    - name: istio-egressgatewaya
      namespace: istio-egress
      enabled: true
      label:
        istio: egressgateway
  meshConfig:
    outboundTrafficPolicy:
      mode: ALLOW_ANY
    meshMTLS:
      minProtocolVersion: TLSV1_3
  values:
    gateways:
      istio-ingressgateway:
        injectionTemplate: gateway
EOF
```

```sh
istioctl install --set profile=default  -f override.yaml
```
