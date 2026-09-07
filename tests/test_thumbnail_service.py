from src.thumbnail_service import PaymentImage, create_thumbnail


class FakeClient:
    def __init__(self):
        self.calls = []

    def upload(self, image, filename):
        self.calls.append(("upload", filename))
        return {"id": "img_123"}

    def process(self, image, width, height):
        self.calls.append(("process", image, width, height))
        return {"url": "https://cdn.example/thumb.webp", "width": width, "height": height}


def test_payment_thumbnail_records_audit_event():
    client = FakeClient()
    result = create_thumbnail(PaymentImage("pay_7", "receipt.png", b"bytes"), client)
    assert result["payment_id"] == "pay_7"
    assert result["audit"] == "thumbnail_created"
    assert client.calls == [("upload", "receipt.png"), ("process", "img_123", 320, 180)]
