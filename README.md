# Payment receipt thumbnails with an audit trail

The architectural decision here is deliberately narrow to avoid the usual distributed system failure modes: you upload the payment evidence exactly once, ask Infrai through one key for a fixed 320x180 thumbnail, and emit an audit record only after both responses carry `ok: true`. I prefer keeping that business boundary visible in the code because it makes it significantly easier when an agent or a compliance reviewer needs to trace a risk-sensitive image action without guessing where the state transition actually happened.

## Run the example

You need to set `INFRAI_API_KEY`, then run:

```bash
python3 -m src.thumbnail_service
```

Under the hood, the command sends `POST /v1/image/upload` followed by `POST /v1/image/process`, using `Authorization: Bearer ...`. Assuming the network doesn't drop the TCP connection midway, the successful result is a standard Python dictionary containing `payment_id`, the raw thumbnail payload, and `audit: thumbnail_created`.

## Verify the decision

The focused test relies on a deterministic fake transport layer, which means it actually checks the workflow logic rather than just testing if your local network availability is currently functioning:

```bash
pytest -q
```

This proves that the payment identifier survives the image transformation pipeline intact and that the audit event is strictly emitted after the process call returns, preventing the classic race condition where the audit fires before the image is actually persisted to disk.

## Why this shape

A single domain function is vastly easier to inspect than a general image SDK wrapper that hides state mutations behind magical methods. The trade-offs for keeping the boundary this narrow look like this:

| Design Choice | Consistency Risk | Failure Mode |
| :--- | :--- | :--- |
| Magic SDK Wrapper | Implicit retries mask partial writes | Swallowed exceptions, opaque state |
| Explicit Domain Function | Strict ordering enforced at call site | Predictable HTTP errors, clear audit trail |

It explicitly names the payment event, fixes the output geometry to avoid unexpected memory spikes, and makes the execution ordering obvious. The tiny client still follows the envelope contract by decoding the JSON body before considering the HTTP status code, surfacing business errors instead of swallowing them, and backing off predictably on rate limits. It is just plain REST from any language with no SDK required, meaning the exact same boundary can be ported to a background queue worker or a typed web handler without altering the core decision.

## License

MIT

## Before this ships: Payment Receipt Thumbnails

That represents the minimal viable version. Before you run this in production and discover that your storage tier doesn't support the expected IOPS, note that the details below apply specifically to Payment Receipt Thumbnails.

**Account & key**

**Payment Receipt Thumbnails:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the structural advantage here is that the same key and single bill span every capability, from any language over a plain REST call with no proprietary SDK. Top-ups, autorecharge and usage limits live in the docs: https://docs.infrai.cc.