# API contracts

## Error response v1

The P01 error response is defined in
[`error-response.v1.schema.json`](./error-response.v1.schema.json). For example:

```json
{
  "code": "NOT_FOUND",
  "message": "Request could not be completed.",
  "request_id": "req_404",
  "details": {}
}
```

The body `request_id` must match the `X-Request-ID` response header (here,
`req_404`). This header/body rule is verified by service tests; JSON Schema
validates the body only. The `details` object is extensible.

P01 foundation verification: Ajv validated the schema, example, and boundary
cases; the Project Service error tests passed. Contract compatibility and
breaking-change checks remain open.

## P01 service-to-service contract drafts

- [Project confirmed-fact snapshot v1](./project-fact-snapshot.v1.md) - proposed
  synchronous read from AI Orchestration to Project; not deployed.

## P02 event contract

- [Project facts updated event v1](./project-facts-updated.v1.schema.json) -
  Project outbox producer and AI Orchestration consumer, as identified by the
  approved system architecture. It carries opaque project/fact IDs and the
  pinned fact snapshot version, not fact values. Transport, delivery timing,
  retry policy and actor-context authorization remain open.
