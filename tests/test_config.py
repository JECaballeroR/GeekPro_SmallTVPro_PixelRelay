from pixel_relay.config import DEFAULT_CONFIG


def test_notification_defaults_are_branded():
    assert DEFAULT_CONFIG["custom_title"] == "THANK YOU"
    assert DEFAULT_CONFIG["custom_footer"] == "JECR"
