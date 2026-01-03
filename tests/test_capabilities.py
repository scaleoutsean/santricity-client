from santricity_client.capabilities import resolve_capabilities


def test_default_profile_uses_latest_release():
    profile = resolve_capabilities(None)
    assert profile.label == "12.00"
    assert profile.supports_jwt is True


def test_future_release_sets_flag():
    profile = resolve_capabilities("99.0")
    assert profile.is_future_release is True
    assert profile.legacy_mapping_endpoint == "/volume-mappings"


def test_legacy_release_disables_jwt():
    profile = resolve_capabilities("11.70")
    assert profile.supports_jwt is False
    assert profile.describe_release() == "11.70"
