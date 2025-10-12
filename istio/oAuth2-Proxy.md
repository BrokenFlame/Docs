# oAuth2-Proxy with Istio

Start by blocking access to the app unless the call is via oAuth2-proxy:

```yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: myApp-allow-from-oauth2
  namespace: default
spec:
  selector:
    matchLabels:
      app: myApp
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/default/sa/oauth2-proxy"]
```

Remember that if you are using group/role base access to add a *when* condition that includes the correct fields:
```yaml
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/default/sa/oauth2-proxy"]
    when:
    - key: request.auth.claims[groups]
      values: ["oidc_group_name"]
```

# Force Istio to validate the JWT bear token
```yaml
apiVersion: security.istio.io/v1beta1
kind: RequestAuthentication
metadata:
  name: myApp-Jwt-Validation
  namespace: default
spec:
  selector:
    matchLabels:
      app: myApp
  jwtRules:
  - issuer: https://auth.mycompany.com/realms/<REALM>    # << REPLACE REALM
    jwksUri: https://auth.mycompany.com/realms/<REALM>/protocol/openid-connect/certs
```

So now nothing should be able to access MyApp unless it has a valid JWT and the call has been proxied via oAuth2-Proxy. However if someone sets PeerAuthentication Permisive on the namespace the following will help protect oAuth2-proxy and the application:

```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: oauth2-proxy-dr
  namespace: default
spec:
  host: oauth2-proxy.default.svc.cluster.local
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: myApp-dr
  namespace: default
spec:
  host: myApp.default.svc.cluster.local
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL
```

Now you need a virtual service and a service to route the traffic correctly from the gateway:
```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: myapp-vs
  namespace: default
spec:
  hosts:
  - myapp.mycompany.com
  gateways:
  - istio-ingress/istio-ingressgateway      # e.g. istio-system/cluster-gateway (replace with your gateway)
  http:
  - match:
    - uri:
        prefix: /
    route:
    - destination:
        host: oauth2-proxy.gadet.svc.cluster.local
        port:
          number: 80
---
apiVersion: v1
kind: Service
metadata:
  name: oauth2-proxy
  namespace: gadet
spec:
  selector:
    app: oauth2-proxy
  ports:
  - name: http # assume TLS is terminated in the ingress-gateway
    port: 80
    targetPort: 4180
```

# No deploy oAuth2-Proxy along with the required secrets. Visit https://oauth2-proxy.github.io/oauth2-proxy/configuration/providers for specific IDP configuration.
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: oauth2-proxy-secret
  namespace: gadet
type: Opaque
data:
  # base64 values
  client-secret: <BASE64_CLIENT_SECRET>
  cookie-secret: <BASE64_32BYTE_RANDOM>   # e.g. base64 of 32 random bytes
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: oauth2-proxy
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: oauth2-proxy
  template:
    metadata:
      labels:
        app: oauth2-proxy
    spec:
      serviceAccountName: oauth2-proxy
      containers:
      - name: oauth2-proxy
        image: quay.io/oauth2-proxy/oauth2-proxy:7.5.1  # adapt to your preferred version
        args:
        - --provider=oidc
        - --oidc-issuer-url=https://auth.mycompany.com/realms/<REALM>   # << REPLACE REALM
        - --client-id=<CLIENT_ID>                                      # << REPLACE
        - --client-secret-file=/etc/secrets/client-secret
        - --cookie-secret-file=/etc/secrets/cookie-secret
        - --redirect-url=https://myapp.mycompany.com/oauth2/callback
        - --email-domain=mycompany.com,anothercompany.com, # "*" can be used as a wild card .mycompany.com would include all subdomains of the domain mycompany
        - --upstreams=http://myapp.default.svc.cluster.local:80
        - --oidc-groups-claim=groups
        - --allowed-group=groupy
        - --pass-access-token=true
        - --set-authorization-header=true
        - --cookie-secure=true
        - --cookie-samesite=lax
        - --http-address=0.0.0.0:4180
        ports:
        - containerPort: 4180
        volumeMounts:
        - name: secrets
          mountPath: /etc/secrets
          readOnly: true
      volumes:
      - name: secrets
        secret:
          secretName: oauth2-proxy-secret
---
```
Remember oAuth2-Proxy can terminate the TLS connection itself if you are not using istio. But the you'll need to use 

Finally update the gateway to forward the traffic to the service.
```yaml
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: istio-ingressgateway
  namespace: istio-ingress
spec:
  selector:
    istio: istio-ingress/ingressgateway  # matches your ingress gateway pod label
  servers:
  - port:
      number: 443
      name: https-myapp
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: myApp-tls-secret  # Kubernetes Secret containing TLS cert/key
    hosts:
    - myapp.mycompany.com
```



