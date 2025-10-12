# Exporter configuration for Kubernetes Logs

```yaml
apiVersion: opentelemetry.io/v1alpha1
kind: OpenTelemetryCollector
metadata:
  name: eks-otel-collector
  namespace: default  # or observability or where the operator is running
spec:
  mode: daemonset      # or deployment if you're collecting metrics, not logs
  config: |
    receivers:
      filelog:
        include: [/var/log/containers/*.log]
        start_at: beginning
        operators:
          - type: json_parser
            id: parse-json
            parse_from: body
            timestamp:
              parse_from: attributes.time
              layout: '%Y-%m-%dT%H:%M:%S.%LZ'
    
    processors:
      k8sattributes:
        auth_type: serviceAccount
        extract:
          metadata:
            - k8s.node.name
            - k8s.namespace.name
            - k8s.pod.name
            - k8s.pod.uid
            - k8s.container.name
            - k8s.container.image.tag
            - k8s.pod.labels
            - k8s.pod.annotations
            - k8s.deployment.name
            - k8s.replicaset.name
            - k8s.statefulset.name
            - k8s.cronjob.name
            - k8s.cronjob.name
      resource:
        attributes:
          - key: cluster.name
            value: your-cluster-name
            action: upsert

      batch:
        send_batch_size: 512         # Number of telemetry items per batch (default is often 512 or 1024)
        timeout: 200ms        # Maximum time to wait before sending a batch (default is often 200ms or 1s)  
    
    exporters:
      datadog:
        api:
          key: "${DD_API_KEY}"
        site: "datadoghq.com"  # Use "datadoghq.eu" if in EU region
        logs:
          enabled: true
    
      loki:
        endpoint: https://logs-prod3.grafana.net/loki/api/v1/push
        headers:
          "Authorization": "Bearer YOUR_GRAFANA_CLOUD_API_KEY"
        labels:
          job: "eks-logs"
          cluster: "your-cluster-name"
    
    service:
      pipelines:
        logs:
          receivers: [filelog]
          processors: [k8sattributes, resource, batch]
          exporters: [datadog, loki]
    ```

* Note annotation and lable detection is not automatic. You need to specify these as k8s.pod.labels.<label_name> for each entry you want to pick up.
