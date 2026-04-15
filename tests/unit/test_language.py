from app.utils.language import detect_language


def test_language_detection_falls_back_to_english() -> None:
    assert detect_language("12345 ???", default="en") == "en"


def test_language_detection_detects_spanish() -> None:
    assert detect_language("Hola, ¿qué es Kubernetes?") == "es"
