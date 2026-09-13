## Ensure external metrics endpoint is not already in use

```sh
kubectl get apiservice v1beta1.external.metrics.k8s.io
```

If DataDog Agent is installed patch DataDog Agent so not to use external metrics endpoint
```sh
# Get Datadog Agent installation name
kubectl get datadogagent -n datadog

## kubectl edit datadogagent datadog -n datadog
kubectl patch datadogagent datadog --type=merge -p '{"spec":{"features":{"externalMetricsServer": { "enabled": "false"}}}}
```sh

## Install Keda
The Keda Operator requires a AWS Role with a trust, this is the IRSA trust example
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::<AWS Account>:oidc-provider/oidc.eks.<AWS Region Code>.amazonaws.com/id/<OIDC ID>"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "oidc.eks.<AWS Region Code>.amazonaws.com/id/<OIDC ID>:sub": "system:serviceaccount:keda:keda-operator",
                    "oidc.eks.<AWS Region Code>.amazonaws.com/id/<OIDC ID>:aud": "sts.amazonaws.com"
                }
            }
        }
    ]
}
```

ArgoCD Project example for KEDA Agent using IRSA
```yaml
project: infrastructure
source:
  repoURL: https://kedacore.github.io/charts
  targetRevision: 2.20.2
  helm:
    parameters:
      - name: podIdentity.aws.irsa.enabled
        value: 'true'
      - name: podIdentity.aws.irsa.roleArn
        value: arn:aws:iam::<AWS Account Number>:role/svc-keda-operator
  chart: keda
destination:
  server: https://kubernetes.default.svc
  namespace: keda
syncPolicy:
  automated:
    prune: true
    selfHeal: true
  syncOptions:
    - Replace=true
    - CreateNamespace=true
```



## Helm Template for KEDA ScaledObject

```yaml
{{- if .Values.keda.enabled }}

---
apiVersion: keda.sh/v1alpha1
kind: TriggerAuthentication
metadata:
  name: {{ include "mychart.name" . }}-trigger-authentication
spec:
  podIdentity:
    provider: aws
    roleArn: {{ required "triggerAuthentication.roleArn is required." .Values.triggerAuthentication.roleArn }}
---

{{- with .Values.scaledObjects }}
{{- if or (not (hasKey . "enabled")) .enabled }}
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: {{ include "common.names.fullname" $ }}-scaledobject
  namespace: {{ $.Release.Namespace }}
  labels:
    {{- include "mychart.labels" $ | nindent 4 }}
spec:
  {{- omit . "triggers" "enabled" | toYaml | nindent 2 }}
  triggers:
  {{- range $t := .triggers }}
  - type: {{ $t.type }}
    {{- with $t.metricType}}
    metricType: {{ . }}
    {{- end }}
    {{- if $t.authenticationRef }}
    authenticationRef:
      name: {{ include "mychart.name" $ }}-trigger-authentication
    {{- end }}
    metadata:
      {{- range $key, $value := $t.metadata }}
      {{ $key }}: {{ $value | quote }}
      {{- end }}
  {{- end }}
{{- end }}
{{- end }}
{{- end }}
```
