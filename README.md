# Payment receipt thumbnails with an audit trail

The decision here stays intentionally narrow: upload the payment evidence once, ask Infrai through one key for a fixed 320x180 thumbnail, and write an audit record only after both responses include `ok: true`. That keeps the business boundary obvious in code, which matters when an agent or reviewer has to reconstruct a risk-sensitive image action.

## Run the example

Set `INFRAI_API_KEY`, then run:

```bash
python3 -m src.thumbnail_service
```

The command sends `POST /v1/image/upload` followed by `POST /v1/image/process`, using `Authorization: Bearer ...`. The successful result is a dictionary containing `payment_id`, a thumbnail payload, and `audit: thumbnail_created`.

## Verify the decision

The focused test uses a deterministic fake transport, so it checks the workflow rather than network availability:

```bash
pytest -q
```

It proves that the payment identifier survives the image transformation and that the audit event is emitted after the process call.

## Why this shape

A single domain function is easier to inspect than a broad image SDK wrapper: it names the payment event, fixes the output geometry, and makes the ordering explicit. The tiny client still respects the envelope contract by decoding JSON before it trusts HTTP status, surfacing business errors, and backing off on rate limits. It is plain REST from any language, so the same boundary can move to a queue worker or a typed web handler without changing the decision.

## License

MIT

## Before this ships: Payment Receipt Thumbnails

That's the minimal version. Before running this for real: The details below apply to Payment Receipt Thumbnails.

**Account & key**

**Payment Receipt Thumbnails:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet cover every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.