# Standard Kubernetes Labels

The newer standard for Kubernetes Labels is listed below.
```sh
app.kubernetes.io/name: The name of the application (e.g., wordpress).

app.kubernetes.io/instance: A unique string to identify a specific instance of an application (e.g., wordpress-abcxy).

app.kubernetes.io/version: The current version of the application (e.g., 4.8.0).

app.kubernetes.io/component: The component within the architecture (e.g., database, api-server).

app.kubernetes.io/part-of: The name of a higher-level application this one is part of (e.g., wordpress-blog).
```

The older standard for labels are:
```sh
release: Identifies the iteration or version tag (e.g., release: stable).

env / environment: Identifies the deployment stage (e.g., env: prod, environment: staging).

owner: Identifies the team or person responsible (e.g., owner: devops-team).

tier: Identifies the architectural layer (e.g., tier: frontend, tier: cache, tier: backend).

role: Identifies the specific job of a pod (e.g., role: worker, role: leader).
```

The below have been deprecated
```sh
app: Identifies the application name (replaced officially by app.kubernetes.io/name).

version: Identifies the software version (replaced officially by app.kubernetes.io/version).
```
