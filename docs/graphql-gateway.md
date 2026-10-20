# Reference GraphQL Read Gateway

`tools/graphql-gateway/gateway.py` (stdlib only) serves a GraphQL query subset
over the indexer corpus (issue #1444). The SDL lives in
`tools/graphql-gateway/schema.graphql`, generated from the event field table
and `KNOWN_TYPES` in `tools/compliance-report/generate.py`; CI-style check:

```
python3 tools/graphql-gateway/gateway.py schema --check tools/graphql-gateway/schema.graphql
```

## Cost limits

| Limit | Value |
| --- | --- |
| Depth | 3 |
| Complexity | 1000 (a list field costs `1 + limit * child cost`) |
| `limit` argument | 0–100 (default 10) |

Over-limit queries fail with an error naming the limit, before any scan.

## Read-only

The schema has no `Mutation` or `Subscription`; the executor rejects any
operation except `query`; the corpus is opened read-only.

## Example queries

```
python3 tools/graphql-gateway/gateway.py query corpus.jsonl '{ events(type: "score", limit: 5) { wallet score ledger } }'
python3 tools/graphql-gateway/gateway.py query corpus.jsonl '{ eventCount(type: "governance_action") }'
python3 tools/graphql-gateway/gateway.py query corpus.jsonl '{ events(type: "score", limit: 2) { wallet related(limit: 3) { type ledger } } }'
```

Tests: `cd tools/graphql-gateway && python3 -m unittest`.
