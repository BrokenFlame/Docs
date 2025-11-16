# Coraza WASM Plugin
Corzaz is an WASM plugin that can be integrated into Istio.

# Check the labels for you Istio ingress and ensure the label selector matches. The following two are pretty standard.
```yaml
spec:
  selector:
    matchLabels:
      app: istio-ingressgateway
```
or
```yaml
spec:
  selector:
    matchLabels:
      istio: ingressgateway
```

# Check your websites still work
Run curl commands such as and ensure you get expected responses using in the 200 range.
```sh
curl -I https://your-domain/
curl -I https://your-domain/health
curl -I https://your-domain/api/products

```

# Run the test script
Download the testscript and name is something appropriate.  Note that this script is only designed to work in Bash.

Add execution right to the script
```sh
chmod +x test-waf.sh
```
Run the script
```sh
./test-waf.sh https://your-ingress-domain
```

