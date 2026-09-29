from uuid import uuid4

from app.core.security import create_access_token, decode_user_id, hash_password, verify_password


def test_password_hashing_round_trip() -> None:
    hashed_password = hash_password("secure-password-123")

    assert hashed_password != "secure-password-123"
    assert verify_password("secure-password-123", hashed_password)
    assert not verify_password("wrong-password", hashed_password)


def test_access_token_round_trip() -> None:
    user_id = uuid4()
    token = create_access_token(user_id)

    assert decode_user_id(token, expected_type="access") == user_id
