Configure Istio Default Gateway to use NLB and allow egress

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
      enabled: true
      k8s:
        serviceAnnotations:
          service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
          service.beta.kubernetes.io/aws-load-balancer-internal: "false"  # or "true" for internal
        service:
          type: LoadBalancer
EOF

```sh
istioctl install --set profile=demo --set meshConfig.outboundTrafficPolicy.mode=ALLOW_ANY --values=override.yaml -f override.yaml 
```
