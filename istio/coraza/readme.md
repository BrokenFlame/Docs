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

