## This is a quick Lease Object template.

Optional Service Account, if the replica set doesn't already have a Service Account.
```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: app-service-account
  namespace: default
```

The lease object is optional if you allow create and delete on the lease object in the role.
```yaml
apiVersion: coordination.k8s.io/v1
kind: Lease
metadata:
  name: my-app-lease
  namespace: default
```

The role is allows access to the leases objects. You may wish to add verbs **"create"** and **"delete"**, if the application uses those verbs on the lease object.

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: lease-holder-role
  namespace: default
rules:
- apiGroups: ["coordination.k8s.io"]
  resources: ["leases"]
  resourceNames: ["my-app-lease"] # Restricts permissions strictly to this named lease
  verbs: ["get", "update"]
```

The role binding to attach the role to the service account to be used by the application.
```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: lease-holder-binding
  namespace: default
subjects:
- kind: ServiceAccount
  name: app-service-account
  namespace: default
roleRef:
kind: Role
  name: lease-holder-role
  apiGroup: rbac.authorization.k8s.io
```
