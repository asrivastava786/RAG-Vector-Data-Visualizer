from app.core.security import hash_password, verify_password


def test_password_hashing_roundtrip() -> None:
    hashed = hash_password("ChangeMeDemo123!")
    assert hashed != "ChangeMeDemo123!"
    assert verify_password("ChangeMeDemo123!", hashed)

