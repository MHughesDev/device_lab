# skills/devops/deploy-to-kubernetes.md

## Purpose

Deploy a product initialized from this template to Kubernetes. Covers environment setup, secrets injection, database configuration, migration management, and troubleshooting deployment failures.

## When to Invoke

- First deployment of a newly initialized product to Kubernetes
- Adding a new environment (dev/staging/prod)
- Troubleshooting deployment failures
- Migrating between cloud providers or Kubernetes clusters
- Setting up CI/CD for automated deployments

## Prerequisites

- Read root `AGENTS.md` and complete mandatory skill search
- Cloud provider account with Kubernetes cluster running
- Domain purchased and DNS configured
- kubectl configured locally and can connect to cluster
- Repository has working CI/CD or images built locally
- Decision on secrets management approach (GitHub Secrets, External Secrets Operator, or Sealed Secrets)

## Time Estimate

- New environment setup: 2-4 hours
- Troubleshooting: 30-60 minutes
- CI/CD configuration: 1-2 hours

---

## Step-by-Step Method

### Phase 1: Validate Prerequisites (10 minutes)

Before starting, verify:

1. **Cluster access:**
   ```bash
   kubectl get nodes
   kubectl get namespaces
   ```

2. **Domain DNS:**
   ```bash
   dig api.yourdomain.com
   # Should resolve to load balancer IP
   ```

3. **Container registry access:**
   ```bash
   docker pull ghcr.io/org/repo:latest
   # Or verify in CI that push succeeded
   ```

4. **Required files exist:**
   ```bash
   ls deploy/k8s/overlays/staging/kustomization.yaml
   ls deploy/k8s/overlays/prod/kustomization.yaml
   ```

If any check fails, stop and fix before proceeding.

---

### Phase 2: Configure Environment-Specific Settings (20 minutes)

#### Step 2.1: Customize Kustomize Overlays

**Staging Overlay:**

Edit `deploy/k8s/overlays/staging/kustomization.yaml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - ../../base

namespace: staging  # Must match environment

# CRITICAL: Update image references
images:
  - name: template-api
    newName: ghcr.io/YOUR_ORG/YOUR_REPO/api  # UPDATE THIS
    newTag: latest
  - name: template-frontend
    newName: ghcr.io/YOUR_ORG/YOUR_REPO/frontend  # UPDATE THIS
    newTag: latest

# Optional: Adjust replica count for staging
replicas:
  - name: api
    count: 1  # Staging: single replica is fine

configMapGenerator:
  - name: api-config
    behavior: merge
    literals:
      - ENVIRONMENT=staging
      - DOMAIN=staging.YOURDOMAIN.com  # UPDATE THIS
      - FRONTEND_HOST=https://staging.YOURDOMAIN.com  # UPDATE THIS
```

**Production Overlay:**

Similar changes, but:
- `namespace: prod`
- `count: 3` (or more for high availability)
- Production domain values

#### Step 2.2: Verify Overlay Builds

```bash
# Test staging overlay
kustomize build deploy/k8s/overlays/staging > /tmp/staging.yaml
# Inspect /tmp/staging.yaml for correctness

# Test production overlay  
kustomize build deploy/k8s/overlays/prod > /tmp/prod.yaml
```

Both should produce valid Kubernetes YAML without errors.

---

### Phase 3: Secrets Management (30-45 minutes)

Choose ONE approach and follow it completely:

---

#### Option A: GitHub Environment Secrets (Recommended for MVP)

**Step 3A.1: Generate Secrets**

```bash
# Generate cryptographically secure values
export SECRET_KEY=$(openssl rand -hex 32)
export POSTGRES_PASSWORD=$(openssl rand -hex 16)
export FIRST_SUPERUSER_PASSWORD=$(openssl rand -hex 16)

# Print for copying to GitHub (don't save to file!)
echo "SECRET_KEY: $SECRET_KEY"
echo "POSTGRES_PASSWORD: $POSTGRES_PASSWORD"
```

**Step 3A.2: Add to GitHub Repository**

Navigate to:
```
Repository → Settings → Environments → New environment
```

Create two environments:
- `staging`
- `production`

Add these secrets to EACH environment (values should be different per environment):

| Secret Name | Value | How to Generate |
|-------------|-------|-----------------|
| `SECRET_KEY` | 64-char hex | `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | 32-char hex | `openssl rand -hex 16` |
| `FIRST_SUPERUSER_PASSWORD` | 32-char hex | `openssl rand -hex 16` |
| `SMTP_PASSWORD` | API key | From SendGrid/AWS SES/etc. |
| `SENTRY_DSN` | DSN URL | From sentry.io project settings |
| `KUBECONFIG` | base64 kubeconfig | `cat ~/.kube/config \| base64` |

**Step 3A.3: Verify CI/CD Integration**

The template's `.github/workflows/cd.yml` already references these secrets. Verify the deployment step includes secret injection.

**Step 3A.4: Deploy Secrets Manually (if not using CI/CD)**

```bash
# For staging
kubectl create namespace staging --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret generic api-secrets \
  --from-literal=SECRET_KEY="$SECRET_KEY" \
  --from-literal=POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
  --from-literal=FIRST_SUPERUSER_PASSWORD="$FIRST_SUPERUSER_PASSWORD" \
  --from-literal=SMTP_PASSWORD="$SMTP_PASSWORD" \
  --from-literal=SENTRY_DSN="$SENTRY_DSN" \
  --namespace=staging \
  --dry-run=client -o yaml | kubectl apply -f -

# Verify
kubectl get secrets -n staging api-secrets -o yaml
```

---

#### Option B: External Secrets Operator

**When to use:** Compliance requirements, multiple services, production at scale

**Quick Start:**

1. **Install External Secrets Operator:**
   ```bash
   helm repo add external-secrets https://charts.external-secrets.io
   helm install external-secrets external-secrets/external-secrets \
     --namespace external-secrets \
     --create-namespace
   ```

2. **Configure Cloud Provider Access** (AWS example):
   - Create IAM role with SecretsManagerReadWrite policy
   - Configure IRSA (IAM Roles for Service Accounts)

3. **Store Secrets in AWS Secrets Manager:**
   ```bash
   aws secretsmanager create-secret \
     --name staging/api/SECRET_KEY \
     --secret-string "$SECRET_KEY"
   ```

4. **Create ExternalSecret Resource:**
   ```yaml
   apiVersion: external-secrets.io/v1beta1
   kind: ExternalSecret
   metadata:
     name: api-secrets
     namespace: staging
   spec:
     refreshInterval: 1h
     secretStoreRef:
       kind: ClusterSecretStore
       name: aws-secrets-manager
     target:
       name: api-secrets
     data:
       - secretKey: SECRET_KEY
         remoteRef:
           key: staging/api/SECRET_KEY
   ```

See `docs/security/secrets-management.md` for detailed setup.

---

#### Option C: Sealed Secrets (GitOps)

**When to use:** GitOps workflows (Flux/ArgoCD), multi-cloud, air-gapped

**Quick Start:**

1. **Install Sealed Secrets Controller:**
   ```bash
   helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
   helm install sealed-secrets sealed-secrets/sealed-secrets \
     --namespace kube-system
   ```

2. **Install kubeseal CLI:**
   ```bash
   # macOS
   brew install kubeseal
   
   # Linux
   wget https://github.com/bitnami-labs/sealed-secrets/releases/download/v0.24.0/kubeseal-linux-amd64 -O kubeseal
   chmod +x kubeseal
   sudo mv kubeseal /usr/local/bin/
   ```

3. **Create and Encrypt Secret:**
   ```bash
   # Create regular secret
   kubectl create secret generic api-secrets \
     --from-literal=SECRET_KEY="$SECRET_KEY" \
     --dry-run=client -o yaml > /tmp/secret.yaml
   
   # Encrypt with cluster's public key
   kubeseal --format yaml < /tmp/secret.yaml > deploy/k8s/overlays/staging/sealed-secret.yaml
   
   # Remove unencrypted file
   rm /tmp/secret.yaml
   
   # Commit the sealed secret (safe to commit!)
   git add deploy/k8s/overlays/staging/sealed-secret.yaml
   ```

---

### Phase 4: Database Configuration (20-30 minutes)

#### Step 4.1: Provision Managed Database

If not already done, provision a managed PostgreSQL instance:

**DigitalOcean:**
- UI: Create → Databases → PostgreSQL
- Select version 16, smallest instance for staging
- Note the connection string

**AWS RDS:**
```bash
aws rds create-db-instance \
  --db-instance-identifier staging-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --allocated-storage 20 \
  --master-username postgres \
  --master-user-password "$POSTGRES_PASSWORD"
```

**GCP Cloud SQL:**
```bash
gcloud sql instances create staging-db \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --storage-size=20GB
```

#### Step 4.2: Configure Connection

Get connection details from your provider:
- Host (e.g., `staging-db.ondigitalocean.com`)
- Port (usually 5432, or 25060 for DigitalOcean)
- Database name (e.g., `defaultdb`)
- Username (e.g., `doadmin`)

Update the secret with these values.

#### Step 4.3: Configure Network Access

**Critical:** Database must be reachable from Kubernetes cluster nodes.

**DigitalOcean:**
- Database → Settings → Trusted Sources
- Add your Kubernetes cluster's node IPs

**AWS:**
- RDS → Security Groups
- Add inbound rule allowing cluster security group

**GCP:**
- Cloud SQL → Connections → Authorized networks
- Add cluster node IP ranges

#### Step 4.4: Test Connectivity

```bash
# From local machine
psql "postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_SERVER:$POSTGRES_PORT/$POSTGRES_DB?sslmode=require"

# From Kubernetes cluster
kubectl run -it --rm db-test --image=postgres:16 --restart=Never -- \
  psql "postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_SERVER:$POSTGRES_PORT/$POSTGRES_DB?sslmode=require"
```

Both should connect successfully. If not, check firewall rules, credentials, and SSL mode.

---

### Phase 5: Deploy Application (10-15 minutes)

#### Step 5.1: Database Migrations (First Deploy Only)

**Important:** Run migrations BEFORE deploying application.

```bash
# Set environment variables locally
export POSTGRES_SERVER=...
export POSTGRES_PASSWORD=...
# ... other vars from secret

# Run migrations
cd apps/api
python -m alembic upgrade head
```

Or use Kubernetes job:
```bash
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migrate
  namespace: staging
spec:
  template:
    spec:
      restartPolicy: OnFailure
      containers:
        - name: migrate
          image: ghcr.io/org/repo/api:latest
          command: ["python", "-m", "alembic", "upgrade", "head"]
          envFrom:
            - secretRef:
                name: api-secrets
EOF

kubectl wait --for=condition=complete job/db-migrate -n staging --timeout=5m
```

#### Step 5.2: Deploy via Kustomize

```bash
# Deploy to staging
kubectl apply -k deploy/k8s/overlays/staging

# Wait for rollout
kubectl rollout status deployment/api -n staging --timeout=5m

# Verify pods
kubectl get pods -n staging
```

#### Step 5.3: Verify Deployment

```bash
# Check pods are running
kubectl get pods -n staging
# Should show: STATUS: Running, READY: 1/1

# Check logs
kubectl logs -n staging deployment/api

# Check health endpoint
kubectl port-forward -n staging deployment/api 8000:8000
curl http://localhost:8000/api/v1/utils/health-check/
# Should return: {"status":"ok"}

# Or via ingress (if DNS configured)
curl https://staging.yourdomain.com/api/v1/utils/health-check/
```

---

### Phase 6: Validation & Smoke Testing (20-30 minutes)

#### Step 6.1: Run Automated Health Checks

```bash
make health-check ENV=staging
```

#### Step 6.2: Manual Smoke Tests

Test these flows manually or with scripts:

1. **User Registration:**
   ```bash
   curl -X POST https://staging.yourdomain.com/api/v1/users/signup \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"testpass123","full_name":"Test User"}'
   ```

2. **Login:**
   ```bash
   curl -X POST https://staging.yourdomain.com/api/v1/login/access-token \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=test@example.com&password=testpass123"
   ```

3. **Authenticated Request:**
   ```bash
   curl https://staging.yourdomain.com/api/v1/users/me \
     -H "Authorization: Bearer <token>"
   ```

4. **Create Resource (e.g., Item):**
   ```bash
   curl -X POST https://staging.yourdomain.com/api/v1/items/ \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{"title":"Test Item","description":"Test description"}'
   ```

5. **Password Reset Email (if email configured):**
   - Request reset: POST `/api/v1/password-recovery/{email}`
   - Verify email received in inbox
   - Reset link works

#### Step 6.3: Frontend Testing

If frontend deployed:
- Navigate to `https://app.staging.yourdomain.com`
- Verify login page loads
- Test complete user flows

---

### Phase 7: Production Deployment (15 minutes)

**⚠️ Only proceed after staging is fully verified.**

#### Step 7.1: Production-Specific Checks

- [ ] Secrets configured in GitHub Environment `production`
- [ ] Database provisioned and accessible
- [ ] Domain DNS points to production load balancer
- [ ] SSL certificate will auto-provision (Let's Encrypt)

#### Step 7.2: Deploy to Production

**Via CI/CD (Recommended):**
```bash
git tag -a v0.1.0 -m "Initial production release"
git push origin v0.1.0
```

GitHub Actions will:
1. Build and push images
2. Deploy to staging (auto)
3. Run smoke tests
4. Deploy to production (manual approval or auto)
5. Verify production health

**Manual (if needed):**
```bash
# Run migrations first
export POSTGRES_SERVER=<prod-db-host>
# ... set other env vars
cd apps/api && python -m alembic upgrade head

# Deploy
kubectl apply -k deploy/k8s/overlays/prod
kubectl rollout status deployment/api -n prod --timeout=10m
```

#### Step 7.3: Post-Deploy Verification

```bash
# Health check
curl https://yourdomain.com/api/v1/utils/health-check/

# Check pods
kubectl get pods -n prod

# Check logs for errors
kubectl logs -n prod deployment/api --tail=100

# Run smoke tests
make smoke-test ENV=production
```

---

## Validation Checklist

Before marking deployment complete:

- [ ] Kubernetes namespace created (staging/prod)
- [ ] Secrets stored in chosen provider (GitHub/External/Sealed)
- [ ] Kubernetes Secrets created in namespace
- [ ] Database accessible from cluster pods
- [ ] Migrations applied successfully
- [ ] Application pods running and ready
- [ ] Health endpoint returns 200 with `{"status":"ok"}`
- [ ] User registration works
- [ ] Login returns valid JWT
- [ ] Authenticated requests succeed
- [ ] Frontend loads (if applicable)
- [ ] TLS certificate valid (not self-signed)
- [ ] Logs aggregating without errors

---

## Common Failure Modes

### Issue: ImagePullBackOff

**Symptoms:** Pod status `ImagePullBackOff`, not starting

**Diagnosis:**
```bash
kubectl describe pod <pod-name> -n staging
# Look for: Failed to pull image, unauthorized, not found
```

**Solutions:**

1. **Image doesn't exist:**
   ```bash
   docker pull ghcr.io/org/repo:tag
   # If fails, image not pushed. Check CI/CD or push manually.
   ```

2. **Authentication failure:**
   - Private registry without `imagePullSecrets`
   - Fix: Add registry credentials as secret

3. **Wrong image tag:**
   - Check `kustomization.yaml` image tag matches pushed tag
   - Use `latest` tag only for development, specific SHAs for production

---

### Issue: CrashLoopBackOff

**Symptoms:** Pod starts, crashes, restarts repeatedly

**Diagnosis:**
```bash
kubectl logs -n staging deployment/api --previous
# Or for current instance:
kubectl logs -n staging deployment/api
```

**Common Causes:**

1. **Database connection failure:**
   ```
   sqlalchemy.exc.OperationalError: could not connect to server: Connection refused
   ```
   - Check `POSTGRES_SERVER` is correct
   - Verify network access (security groups/firewall)
   - Confirm SSL mode (managed DBs usually require SSL)

2. **Missing required environment variable:**
   ```
   pydantic.error_wrappers.ValidationError: field required: SECRET_KEY
   ```
   - Check all required secrets are in Kubernetes Secret
   - Verify `envFrom: secretRef` in deployment

3. **Migration not run:**
   ```
   sqlalchemy.exc.ProgrammingError: relation "user" does not exist
   ```
   - Run migrations: `make migrate ENV=staging`

4. **Port binding issue:**
   - Check container listens on port 8000
   - Verify `containerPort: 8000` in deployment

---

### Issue: Pending Pods

**Symptoms:** Pod status `Pending` indefinitely

**Diagnosis:**
```bash
kubectl describe pod <pod-name> -n staging
# Look for: Insufficient cpu, Insufficient memory, Unschedulable
```

**Solutions:**

1. **Insufficient resources:**
   - Check node capacity: `kubectl top nodes`
   - Reduce resource requests in deployment, or
   - Scale cluster: Add nodes or larger instance types

2. **Taints/tolerations mismatch:**
   - Check node taints: `kubectl get nodes -o yaml | grep taints`
   - Add tolerations to deployment or remove taints

3. **Persistent Volume not bound:**
   - If using PVCs, check storage class exists
   - Verify volume provisioner is running

---

### Issue: Service Unreachable (502/503 errors)

**Symptoms:** Health check fails, ingress returns 502

**Diagnosis:**
```bash
# Check if pod is ready
kubectl get pods -n staging
# READY column should be 1/1

# Check readiness probe
kubectl describe pod <pod> -n staging
# Look for: Readiness probe failed

# Check service endpoints
kubectl get endpoints -n staging
# Should show pod IPs
```

**Solutions:**

1. **Readiness probe failing:**
   - Check application is actually healthy
   - Verify `/api/v1/utils/health-check/` returns 200
   - Adjust probe timing if app is slow to start

2. **Service selector mismatch:**
   - Check deployment labels match service selector
   - Verify `app: api` label consistency

3. **Ingress misconfiguration:**
   - Check ingress rules match domain
   - Verify TLS secret exists if using HTTPS
   - Check backend service port matches container port

---

### Issue: Database Migration Failures

**Symptoms:** Migration job fails, app won't start

**Diagnosis:**
```bash
kubectl logs job/db-migrate -n staging
# Or:
cd apps/api && alembic upgrade head --sql  # Dry run to see SQL
```

**Solutions:**

1. **Connection failure:**
   - Verify credentials in secret
   - Test connectivity from pod
   - Check SSL mode (managed DBs often require `sslmode=require`)

2. **Migration conflict:**
   - Check `alembic history` for branching
   - Merge heads: `alembic merge heads`
   - Or stamp and recreate: `alembic stamp <revision>` then `alembic upgrade head`

3. **Irreversible migration:**
   - Test downgrade before production: `alembic downgrade -1`
   - Keep backups before major migrations

---

## Handoff Expectations

After completing this skill:

### Document in PR/Notes:
1. **Cloud provider and region** chosen
2. **Domain** configured
3. **Secrets approach** selected (A, B, or C)
4. **Database** provider and connection method
5. **Any deviations** from standard procedure (ADRs if significant)

### Commands Run (with key output):
```bash
# Example format for handoff
$ kubectl get nodes
NAME           STATUS   ROLES    AGE   VERSION
pool-1-abc12   Ready    <none>   1h    v1.29.1
pool-1-abc34   Ready    <none>   1h    v1.29.1

$ kubectl get pods -n staging
NAME                    READY   STATUS    RESTARTS   AGE
api-7c9f4b8d5-2k4m9    1/1     Running   0          15m
```

### Files Changed:
- `deploy/k8s/overlays/staging/kustomization.yaml`
- `deploy/k8s/overlays/prod/kustomization.yaml`
- `.github/workflows/cd.yml` (if modified)
- `docs/adr/0002-deployment-decisions.md` (if created)

### Residual Risks:
- List any incomplete steps or known issues
- Note any manual steps that should be automated

### Follow-ups:
- Monitoring setup
- Backup verification
- Team training on procedures

---

## Related Skills and Documents

| Resource | Purpose |
|----------|---------|
| `docs/operations/deployment.md` | Ongoing deployment procedures |
| `docs/procedures/cloud-deployment-setup.md` | Full setup procedure |
| `docs/procedures/pre-deploy-checklist.md` | Pre-flight validation |
| `docs/security/secrets-management.md` | Secrets approach details |
| `docs/operations/runbooks/rollback.md` | Emergency rollback |
| `docs/operations/runbooks/database-recovery.md` | Database recovery |
| `skills/devops/k8s-probes.md` | Kubernetes probe configuration |
| `skills/devops/rollout-rollback.md` | Rollout and rollback procedures |
| `skills/devops/backup-restore-drills.md` | Backup verification |

---

## Validation Checklist for This Skill

- [ ] Cluster accessible via kubectl
- [ ] Domain DNS resolves correctly
- [ ] Secrets stored securely (not in Git)
- [ ] Kubernetes Secrets created in namespace
- [ ] Database migrations applied
- [ ] Application pods running and ready
- [ ] Health checks return 200
- [ ] Smoke tests pass
- [ ] Can register user and login
- [ ] Logs accessible without errors
