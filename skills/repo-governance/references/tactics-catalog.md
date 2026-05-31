# skills/repo-governance/references/tactics-catalog.md

**Purpose:** Quality-attribute → tactics lookup table used by `skills/repo-governance/architecture-design.md` Stage 2 Step 3. For each quality attribute (performance, availability, security, modifiability, …), this file lists the concrete architectural tactics that directly affect a system's ability to achieve it. This file is reference material, not an invocable skill on its own.

## When to invoke

- From `architecture-design.md` Stage 2 Step 3 when mapping a prioritized quality attribute to concrete tactics for the current decision.
- Standalone, when reviewing an existing module to assess which tactics are in play vs missing.

## Prerequisites

- The quality attributes that matter to the current decision are already prioritized (Stage 1 output of `architecture-design.md`).
- You have read enough of the targeted attribute's section here to recognize which tactics apply to the current context.

## Reference

For each quality attribute, the concrete architectural tactics — design decisions that directly affect the system's ability to achieve that attribute.

Source: Bass, Clements & Kazman — *Software Architecture in Practice* (SEI/CMU), and Cervantes & Kazman — *Designing Software Architectures* (ADD method, Addison-Wesley 2016).

---

## Performance

**Goal**: control response time and throughput under expected and peak load.

### Resource Demand Tactics
- **Manage sampling rate** — reduce frequency of data collection or event processing
- **Limit event response** — queue or shed excess load beyond a defined threshold
- **Prioritize events** — process high-priority requests ahead of low-priority ones
- **Reduce computational overhead** — eliminate redundant processing; cache derived results
- **Bound execution times** — enforce timeouts; limit iteration depth in algorithms
- **Increase resource efficiency** — choose better algorithms; reduce memory allocations

### Resource Supply Tactics
- **Increase resources** — add CPUs, memory, faster disks, higher bandwidth
- **Introduce concurrency** — process requests in parallel; use thread pools or async I/O
- **Maintain multiple copies of data** — read replicas, CDN caches, materialized views
- **Maintain multiple copies of computation** — horizontal scaling; replicated workers
- **Schedule resources** — choose scheduling policies (FIFO, priority queue, round-robin)

### Patterns that Apply
- **CQRS** — separate read and write models to optimize each independently
- **Event sourcing** — append-only log enables efficient replay and read projections
- **Sidecar / Ambassador** — offload cross-cutting work (auth, compression) to a proxy

---

## Availability

**Goal**: minimize downtime and ensure the system recovers gracefully from faults.

### Fault Detection Tactics
- **Monitor** — heartbeat, ping/echo, sanity check against expected invariants
- **Ping/echo** — periodic liveness check between components
- **Heartbeat** — component periodically signals it is alive
- **Condition monitoring** — watch for resource exhaustion, error rate spikes
- **Voting** — compare outputs from redundant components; majority wins
- **Exception detection** — catch system exceptions; distinguish expected vs. unexpected faults
- **Self-test** — component runs internal diagnostics on startup or periodically

### Fault Recovery Tactics
- **Retry** — retry failed requests with exponential backoff and jitter
- **Redundant spare** — hot standby takes over when primary fails (active-passive)
- **Active redundancy** — parallel identical components all process requests; fastest wins
- **Rollback** — revert to a last-known-good state
- **Ignore faulty behavior** — if a non-critical component fails, degrade gracefully
- **Reconfiguration** — reassign responsibilities to surviving components dynamically
- **Shadow** — run new component in parallel with old, comparing outputs before cutover
- **State resynchronization** — resync replicas after partition or failure

### Fault Prevention Tactics
- **Removal from service** — take a component offline proactively before it fails
- **Transactions** — ensure all-or-nothing semantics for state changes
- **Process monitor** — watchdog restarts crashed processes automatically
- **Prevent exceptions** — validate inputs; use null-safe patterns; avoid unchecked casts

### Patterns that Apply
- **Circuit breaker** — stop sending requests to a failing dependency; fail fast
- **Bulkhead** — isolate failure domains so one component's failure doesn't cascade
- **Saga** — manage distributed transactions with compensating actions

---

## Modifiability

**Goal**: limit the cost and risk of making changes.

### Reduce Module Size
- **Split module** — if a module has multiple responsibilities, separate them
- **Increase cohesion** — each module owns one responsibility end-to-end

### Reduce Coupling
- **Encapsulate** — hide implementation behind a stable interface; callers depend on the interface only
- **Use an intermediary** — broker, facade, or adapter decouples caller from callee
- **Restrict dependencies** — enforce dependency rules (e.g., layers only depend downward)
- **Abstract common services** — shared functionality in a stable, versioned service
- **Co-locate related responsibilities** — things that change together should live together

### Defer Binding
- **Component replacement** — make it easy to swap an implementation behind an interface
- **Configuration** — externalize decisions to config files, env vars, or feature flags
- **Polymorphism** — use interfaces so behavior can be substituted without code changes
- **Publish-subscribe** — producers don't know about consumers; add consumers freely
- **Dependency injection** — inject collaborators at runtime rather than hard-coding them

### Patterns that Apply
- **Hexagonal (Ports & Adapters)** — business logic is isolated from infrastructure details
- **Plugin / extension point** — system core defines extension interfaces; plugins provide implementations
- **Strangler fig** — incrementally replace legacy system without a big-bang rewrite

---

## Security

**Goal**: protect the system from unauthorized access and ensure data integrity.

### Detect Attacks
- **Detect intrusion** — compare traffic against known attack signatures
- **Detect service denial** — monitor for traffic patterns consistent with DoS attacks
- **Verify message integrity** — use checksums, HMAC, or digital signatures
- **Detect message delay** — flag requests with stale or replayed timestamps (nonce/timestamp check)

### Resist Attacks
- **Identify actors** — authenticate every request; never trust implicit identity
- **Authenticate actors** — use strong authentication (MFA, certificate, OAuth2/OIDC)
- **Authorize actors** — enforce least privilege; check permissions at every service boundary
- **Limit access** — network-level isolation; private subnets; API gateways as choke points
- **Limit exposure** — minimize the attack surface; disable unused endpoints and ports
- **Encrypt data** — encrypt data in transit (TLS) and at rest (AES-256)
- **Separate entities** — multi-tenancy isolation; separate data stores per tenant
- **Change default settings** — never ship with default passwords or permissive configs
- **Validate input** — sanitize and validate all external input; reject before processing

### React to Attacks
- **Revoke access** — immediately invalidate tokens/sessions on breach detection
- **Lock computer** — rate limiting, account lockout after N failed attempts
- **Inform actors** — alert operators; produce audit log of all security events
- **Restore state** — have a known-good snapshot to roll back to

### Patterns that Apply
- **Zero-trust** — verify every request regardless of network origin
- **API gateway** — centralized auth, rate limiting, and input validation before traffic reaches services
- **Secret management** — use Vault, AWS Secrets Manager, or equivalent; never hardcode credentials

---

## Scalability / Elasticity

**Goal**: handle growth in load without architectural rework.

### Horizontal Scaling Tactics
- **Stateless services** — store no session state in the process; state lives in a shared store
- **Shared-nothing architecture** — each node is independent; no single point of coordination
- **Partitioning / Sharding** — distribute data and load across independent partitions by key
- **Database read replicas** — route reads to replicas, writes to primary

### Vertical Scaling Tactics
- **Resource upgrade** — increase CPU/RAM/disk on existing instances (limited, but often fastest short-term)

### Load Distribution Tactics
- **Load balancer** — distribute requests across instances using round-robin, least-connections, or IP hash
- **Queue-based load leveling** — decouple producers and consumers via a queue; consumers process at their own pace
- **Auto-scaling** — add/remove instances based on CPU, memory, queue depth, or custom metrics

### Patterns that Apply
- **Event-driven** — async processing absorbs burst load without blocking producers
- **CQRS** — scale reads and writes independently
- **Cell-based architecture** — independent cells limit blast radius and enable per-cell scaling

---

## Testability

**Goal**: make it cheap and fast to detect faults through testing.

### Control and Observe
- **Specialized interfaces** — expose test seams (setters, factories, dependency injection) for unit tests
- **Record/playback** — capture real traffic and replay it in tests
- **Localize state storage** — centralize state so it can be inspected and reset easily
- **Abstract data sources** — depend on interfaces, not concrete DBs, so tests can substitute fakes
- **Sandbox** — isolate test environments from production data and systems

### Limit Complexity
- **Limit nondeterminism** — minimize use of random values, current time, or network calls in core logic
- **Limit coupling** — the less a component knows about its neighbors, the easier it is to test in isolation

---

## Deployability

**Goal**: release changes quickly, safely, and independently.

### Tactics
- **Immutable infrastructure** — replace instances rather than mutate them; no config drift
- **Feature flags** — ship code dark; enable for subsets of users without redeployment
- **Blue/green deployment** — maintain two identical environments; switch traffic atomically
- **Canary release** — route a small traffic percentage to the new version; monitor before full rollout
- **Rolling deployment** — replace instances one at a time; never take the whole system down
- **Health checks** — route traffic only to instances that pass liveness and readiness checks
- **Rollback capability** — every deployment must be reversible in < 5 minutes

### Patterns that Apply
- **Twelve-factor app** — configuration via env vars, stateless processes, disposable containers
- **Service mesh** — traffic management, retries, and circuit breaking as infrastructure, not code

---

## Interoperability

**Goal**: communicate with external systems reliably and without tight coupling.

### Tactics
- **Discover service** — use service registries or DNS-based discovery; avoid hardcoded endpoints
- **Tailor interface** — use adapters to translate between internal models and external contracts
- **Standard interfaces** — prefer open standards (REST, gRPC, OpenAPI, AsyncAPI, CloudEvents)
- **Versioned contracts** — version APIs explicitly; maintain backwards compatibility across versions

---

## Tactic Selection Matrix Template

Use in `architecture-design.md` Stage 2 Step 3. Score each candidate pattern against each driver:

| Candidate Pattern | Perf | Avail | Modif | Sec | Scale | Total |
|---|---|---|---|---|---|---|
| Modular monolith | | | | | | |
| Microservices | | | | | | |
| Event-driven | | | | | | |
| Serverless / FaaS | | | | | | |

Score: 1 = poor fit, 2 = neutral, 3 = strong fit. Weight by 1.5× for high-priority drivers if needed.

**Baseline for this repo**: the default stack (FastAPI modular monolith, single deployment, SQLAlchemy) scores modular monolith highest for most early-stage projects. Microservices only justify their operational overhead when independent deployability is a high-priority architectural driver.
