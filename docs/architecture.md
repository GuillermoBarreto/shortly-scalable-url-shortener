# Shortly architecture

## Request and redirect flows

Creation enters `/api/v1`, where Pydantic accepts only HTTP(S) URLs and normalizes aliases. Authentication is optional for creation and mandatory for management. `LinkService` generates seven-character codes with `secrets`; a unique database constraint is the concurrency-safe authority. Random collisions retry five times and alias collisions return 409.

Management decodes signed expiring JWTs and scopes every lookup to link and owner IDs. CORS is allow-listed, request bodies are bounded, and proxy address headers are ignored unless an operator establishes a trusted proxy boundary.

Redirects apply an abuse limit, consult `link:{code}` in Redis, fall back to the unique database index, reject missing/disabled/expired records, cache valid metadata no longer than one hour or expiration, record privacy-limited analytics, and return 307. Redis errors are logged as cache misses. Updates and deletion invalidate old/new keys.

## Database, analytics, and privacy

Users have UUIDs, unique normalized emails, adaptive password hashes, and aware timestamps. Links have UUIDs, unique codes/aliases, ownership and lifecycle fields, a click counter, and compound owner/created and active/expiry indexes. Click events contain bounded coarse client metadata and a daily visitor hash, indexed by link/time.

Raw IP addresses are never stored. The identifier is SHA-256 of a private salt, UTC date, and address, limiting longitudinal correlation. Country is optional and accepted only from configured trusted infrastructure. Referrer length is bounded; stricter deployments can strip query strings.

Analytics insertion and its counter currently commit together. That favors understandable correctness but adds redirect latency. The next boundary is a durable bounded queue: publish a stable event ID, redirect immediately, consume idempotently, batch inserts, update rollups, and retain replay/dead-letter paths.

## Cache, rate limiting, and reliability

Redis is cache-aside and never authoritative. Its TTL respects link expiration and failures preserve database behavior. The local fallback limiter keeps development functional but is per-process; horizontal deployments should use Redis atomic counters or an edge gateway.

## Horizontal growth

- Hundreds/thousands: one API process, PostgreSQL, optional Redis, transactional analytics.
- Tens/hundreds of thousands: stateless replicas, managed Redis, pooling, analytics queue, scheduled rollups, retention policies.
- Millions: time/hash partitioned events, separate redirect/management workloads, regional caches, dashboard replicas, precomputed aggregates, and edge abuse controls.

Likely bottlenecks are synchronous event writes, hot counters, high-cardinality scans, cache hot keys, then cross-region database latency. Measure p95/p99 redirects, hit ratio, queue lag, collision retries, saturation, and event replay before adding infrastructure.

The modular monolith keeps deployment and transaction boundaries understandable while preserving extraction points. SQLite reduces local friction; PostgreSQL provides production concurrency. JWTs make access checks stateless; refresh rotation/revocation is the appropriate extension for stricter threat models.
