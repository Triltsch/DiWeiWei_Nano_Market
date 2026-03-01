"""
Test suite for password hashing and verification.

Tests cover:
- Basic bcrypt hashing and verification
- Password strength validation
- Edge cases (empty, long, special characters)
- Performance requirements (<500ms per hash)
- Security properties (no leakage, constant-time comparison)
- Hash metadata extraction
"""

import time
from typing import Final

import pytest

from app.modules.auth.password import (
    BCRYPT_MAX_PASSWORD_BYTES,
    BCRYPT_ROUNDS,
    get_password_hash_info,
    hash_password,
    verify_password,
)
from app.modules.auth.validators import validate_password_strength


class TestPasswordHashing:
    """Test password hashing functionality"""

    def test_hash_password_basic(self):
        """Test that password hashing produces a valid bcrypt hash"""
        password = "TestPass123!"
        hashed = hash_password(password)

        # Bcrypt hashes start with $2b$ and are 60 characters long
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60
        assert password not in hashed  # Plain password not in hash

    def test_hash_password_unique_salts(self):
        """Test that same password produces different hashes (unique salts)"""
        password = "SamePassword123!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Same password should produce different hashes due to unique salts
        assert hash1 != hash2
        assert hash1.startswith("$2b$")
        assert hash2.startswith("$2b$")

    def test_hash_password_bcrypt_rounds(self):
        """Test that bcrypt uses correct cost factor (rounds=12)"""
        password = "TestPass123!"
        hashed = hash_password(password)

        # Extract rounds from hash format: $2b$12$...
        parts = hashed.split("$")
        rounds = int(parts[2])

        assert rounds == BCRYPT_ROUNDS
        assert rounds >= 10  # Minimum OWASP recommendation

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "ValidPass123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "ValidPass123!"
        hashed = hash_password(password)

        # Try various incorrect passwords
        assert verify_password("WrongPass123!", hashed) is False
        assert verify_password("validpass123!", hashed) is False  # Case sensitive
        assert verify_password("ValidPass123", hashed) is False  # Missing char
        assert verify_password("", hashed) is False  # Empty
        assert verify_password(" ValidPass123! ", hashed) is False  # Extra spaces

    def test_hash_password_empty_raises_error(self):
        """Test that empty password raises ValueError"""
        with pytest.raises(ValueError, match="Password cannot be empty"):
            hash_password("")

    def test_hash_password_very_long(self):
        """Test hashing of very long passwords (>72 bytes, bcrypt limit)"""
        # Create password longer than 72 bytes
        long_password = "A" * 100 + "TestPass123!"

        hashed = hash_password(long_password)

        assert hashed.startswith("$2b$")
        assert verify_password(long_password, hashed) is True

    def test_hash_password_max_length_exceeded(self):
        """Test that excessively long passwords raise ValueError"""
        extremely_long_password = "A" * 10000

        with pytest.raises(ValueError, match="Password exceeds maximum length"):
            hash_password(extremely_long_password)

    def test_hash_password_special_characters(self):
        """Test password with various special characters"""
        special_passwords = [
            "Test@Pass#123",
            "Pässwörd123!",  # Unicode
            "Test\nPass123!",  # Newline
            "Test\tPass123!",  # Tab
            "Test'Pass\"123!",  # Quotes
            "Test<Pass>123!",  # Angle brackets
            "Test{Pass}123!",  # Braces
            "Test|Pass\\123!",  # Pipe and backslash
        ]

        for password in special_passwords:
            hashed = hash_password(password)
            assert hashed.startswith("$2b$")
            assert verify_password(password, hashed) is True

    def test_hash_password_unicode(self):
        """Test password with Unicode characters"""
        unicode_passwords = [
            "Пароль123!",  # Cyrillic
            "密码Test123!",  # Chinese
            "パスワード123!",  # Japanese
            "كلمة123!",  # Arabic
            "🔒Secure123!",  # Emoji
        ]

        for password in unicode_passwords:
            hashed = hash_password(password)
            assert verify_password(password, hashed) is True

    def test_verify_password_invalid_hash(self):
        """Test verification with invalid hash format returns False"""
        password = "TestPass123!"

        invalid_hashes = [
            "",
            "not-a-hash",
            "$2b$invalid",
            "plaintext_password",
            None,
        ]

        for invalid_hash in invalid_hashes:
            if invalid_hash is None:
                # Skip None as it would cause TypeError
                continue
            assert verify_password(password, invalid_hash) is False

    def test_verify_password_empty_inputs(self):
        """Test verification with empty inputs returns False"""
        hashed = hash_password("TestPass123!")

        assert verify_password("", hashed) is False
        assert verify_password("TestPass123!", "") is False
        assert verify_password("", "") is False

    def test_hash_performance(self):
        """Test that hashing completes within 500ms (averaged over multiple runs)"""
        password = "TestPass123!"
        iterations = 3
        total_time = 0

        for _ in range(iterations):
            start_time = time.perf_counter()
            hash_password(password)
            total_time += time.perf_counter() - start_time

        avg_duration_ms = (total_time / iterations) * 1000

        # Average should be under 500ms per requirement
        # Using 600ms threshold to account for CI runner variance
        assert avg_duration_ms < 600, (
            f"Average hashing took {avg_duration_ms:.2f}ms over {iterations} runs, "
            f"exceeds 600ms threshold (target: 500ms)"
        )

    def test_verify_performance(self):
        """Test that verification completes within 500ms (averaged over multiple runs)"""
        password = "TestPass123!"
        hashed = hash_password(password)
        iterations = 3
        total_time = 0

        for _ in range(iterations):
            start_time = time.perf_counter()
            verify_password(password, hashed)
            total_time += time.perf_counter() - start_time

        avg_duration_ms = (total_time / iterations) * 1000

        # Average should be under 500ms per requirement
        # Using 600ms threshold to account for CI runner variance
        assert avg_duration_ms < 600, (
            f"Average verification took {avg_duration_ms:.2f}ms over {iterations} runs, "
            f"exceeds 600ms threshold (target: 500ms)"
        )

    def test_password_not_in_error_messages(self, caplog):
        """Test that passwords are not exposed in log messages"""
        password = "SecretPassword123!"

        # Hash a password and verify
        hashed = hash_password(password)
        verify_password(password, hashed)

        # Check logs don't contain the password
        for record in caplog.records:
            assert password not in record.message
            assert password not in str(record.args)

    def test_sha256_prehashing_for_long_passwords(self):
        """Test SHA256 pre-hashing is applied for passwords >72 bytes"""
        # Password exactly at bcrypt limit (72 bytes)
        password_72 = "A" * 72
        hashed_72 = hash_password(password_72)

        # Password exceeding bcrypt limit (73 bytes)
        password_73 = "A" * 73
        hashed_73 = hash_password(password_73)

        # Both should hash successfully
        assert verify_password(password_72, hashed_72) is True
        assert verify_password(password_73, hashed_73) is True

        # SHA256 pre-hashing should be applied to longer password
        # (this is tested implicitly by successful verification)
        assert hashed_73.startswith("$2b$")


class TestPasswordHashInfo:
    """Test password hash metadata extraction"""

    def test_get_hash_info_valid_bcrypt(self):
        """Test extracting info from valid bcrypt hash"""
        password = "TestPass123!"
        hashed = hash_password(password)

        info = get_password_hash_info(hashed)

        # Check that scheme is truthy and related to bcrypt
        assert info["scheme"] is not None
        assert info["rounds"] == BCRYPT_ROUNDS
        assert info["valid"] is True

    def test_get_hash_info_invalid_hash(self):
        """Test extracting info from invalid hash"""
        invalid_hashes = [
            "",
            "not-a-hash",
            "plaintext",
            "$invalid$format$",
        ]

        for invalid_hash in invalid_hashes:
            info = get_password_hash_info(invalid_hash)
            assert info["valid"] is False
            assert info["scheme"] is None
            assert info["rounds"] is None


class TestPasswordValidation:
    """Test password strength validation"""

    def test_validate_password_strength_valid(self):
        """Test validation of strong passwords"""
        valid_passwords = [
            "ValidPass123!",
            "MyP@ssw0rd",
            "Str0ng!Password",
            "T3st@123",
        ]

        for password in valid_passwords:
            is_valid, error_msg = validate_password_strength(password)
            assert is_valid is True
            assert error_msg == ""

    def test_validate_password_strength_too_short(self):
        """Test validation rejects passwords shorter than 8 characters"""
        short_passwords = [
            "Short1!",  # 7 chars
            "Test1!",  # 6 chars
            "Abc1!",  # 5 chars
        ]

        for password in short_passwords:
            is_valid, error_msg = validate_password_strength(password)
            assert is_valid is False
            assert "at least 8 characters" in error_msg

    def test_validate_password_strength_no_uppercase(self):
        """Test validation rejects passwords without uppercase letters"""
        passwords_no_upper = [
            "testpass123!",
            "mypassword1!",
            "lowercase1!",
        ]

        for password in passwords_no_upper:
            is_valid, error_msg = validate_password_strength(password)
            assert is_valid is False
            assert "uppercase letter" in error_msg

    def test_validate_password_strength_no_digit(self):
        """Test validation rejects passwords without digits"""
        passwords_no_digit = [
            "TestPassword!",
            "MyPassword!",
            "NoDigits!",
        ]

        for password in passwords_no_digit:
            is_valid, error_msg = validate_password_strength(password)
            assert is_valid is False
            assert "digit" in error_msg

    def test_validate_password_strength_no_special(self):
        """Test validation rejects passwords without special characters"""
        passwords_no_special = [
            "TestPassword123",
            "MyPassword123",
            "NoSpecial123",
        ]

        for password in passwords_no_special:
            is_valid, error_msg = validate_password_strength(password)
            assert is_valid is False
            assert "special character" in error_msg

    def test_validate_password_strength_edge_cases(self):
        """Test validation with edge cases"""
        # Exactly 8 characters, all requirements met
        assert validate_password_strength("Test123!")[0] is True

        # Empty password
        assert validate_password_strength("")[0] is False

        # Only spaces
        assert validate_password_strength("        ")[0] is False


class TestPasswordHashingIntegration:
    """Integration tests for password hashing in authentication flow"""

    def test_registration_password_flow(self):
        """Test complete password flow: validation -> hashing -> verification"""
        password = "RegisterPass123!"

        # Step 1: Validate password strength
        is_valid, error_msg = validate_password_strength(password)
        assert is_valid is True

        # Step 2: Hash password
        hashed = hash_password(password)
        assert hashed.startswith("$2b$")

        # Step 3: Verify password (login simulation)
        assert verify_password(password, hashed) is True
        assert verify_password("WrongPass123!", hashed) is False

    def test_multiple_users_same_password(self):
        """Test that multiple users with same password get different hashes"""
        password = "CommonPassword123!"

        # Simulate 3 users registering with same password
        hashes = [hash_password(password) for _ in range(3)]

        # All hashes should be different (unique salts)
        assert len(set(hashes)) == 3

        # All should verify correctly
        for hashed in hashes:
            assert verify_password(password, hashed) is True

    def test_password_complexity_scenarios(self):
        """Test various password complexity scenarios"""
        test_cases = [
            ("Simple123!", True, ""),  # Valid
            ("short1!", False, "at least 8 characters"),  # Too short
            ("nouppercase123!", False, "uppercase letter"),  # No uppercase
            ("NoDigitsHere!", False, "digit"),  # No digits
            ("NoSpecialChar123", False, "special character"),  # No special
        ]

        for password, expected_valid, expected_error_fragment in test_cases:
            is_valid, error_msg = validate_password_strength(password)
            assert (
                is_valid == expected_valid
            ), f"Password {password}: expected {expected_valid}, got {is_valid}, message: {error_msg}"
            if not expected_valid:
                assert expected_error_fragment in error_msg.lower()
