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
Remember if your app does not have a service account it Kubernetes always assigned the namespace's default service account.

## Allowing remote IP Addresses access to your application
If you want to allow remote IP addresses you may need to update your Istio Ingress configuration and the assoicated Istio Ingress (Kubernetes Services). 

Firstly ensure that at least 1 ingress is running per node, but setting the minium and maxium number of ingress pods.
```yaml
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
        hpaSpec:
          maxReplicas: 21
          minReplicas: 3
        serviceAnnotations:
          service.beta.kubernetes.io/aws-load-balancer-type: "external"
          service.beta.kubernetes.io/aws-load-balancer-nlb-target-type: "ip"
          service.beta.kubernetes.io/aws-load-balancer-scheme: "internet-facing"
          service.beta.kubernetes.io/aws-load-balancer-security-groups: "xxxxx"
        service:
          type: LoadBalancer
```
Once you have done update the service so it perserves the IP address 
```yaml
spec:
  externalTrafficPolicy: Local
```
Now create you policy. Noting to use remoteIpBlocks instead of IpBlocks as the X-Forwarded-Header is where the address of the client will be preserved.
```yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: app-ip-whitelist
  namespace: default
spec:
  selector:
    matchLabels:
      app: webapp
  action: ALLOW
  rules:
  # Allow requests from your public IP
  - from:
    - source:
        remoteIpBlocks: ["194.9.108.83/32"]
  # Allow all traffic from within the mesh
  - from:
    - source:
        principals: ["cluster.local/ns/*/sa/*"]
```
