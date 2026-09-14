from src.extract import classify_document
from src.utils import normalize_url


def test_normalize_url_removes_tracking():
    assert normalize_url("https://Example.com/a/?utm_source=x&x=1#frag") == "https://example.com/a?x=1"


def test_classifier_distinguishes_inference(sqlite_row):
    event = classify_document(sqlite_row)
    assert event.event_type == "CAMPAIGN_LAUNCH"
    assert "Inference" in event.inference_json or "推定" in event.marketing_intent

