from backend.app.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_is_not_plaintext_and_verifies() -> None:
    encoded = hash_password("DemoPass123!")
    assert encoded != "DemoPass123!"
    assert verify_password("DemoPass123!", encoded)
    assert not verify_password("wrong-password", encoded)


def test_access_token_round_trip() -> None:
    assert decode_access_token(create_access_token("42")) == "42"
