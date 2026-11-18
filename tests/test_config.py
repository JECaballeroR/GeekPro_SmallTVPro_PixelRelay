from pixel_relay.config import DEFAULT_CONFIG


def test_notification_defaults_are_branded():
    assert DEFAULT_CONFIG["custom_title"] == "THANK YOU"
    assert DEFAULT_CONFIG["custom_footer"] == "JECR"



def test_pinned_view_defaults_are_safe():
    assert DEFAULT_CONFIG["pinned_view_enabled"] is False
    assert DEFAULT_CONFIG["pinned_view"] == "clock"
