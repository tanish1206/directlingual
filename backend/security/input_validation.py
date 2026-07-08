"""
backend/security/input_validation.py
──────────────────────────────────────
Sanitizes and validates all user input before it reaches the LLM or any
database query.

Sanitization uses the `bleach` library (not hand-rolled regex) to strip HTML.
Bleach is a well-maintained, security-audited allowlist-based sanitizer that
correctly handles edge cases like `<<script>script>`, malformed tags, and
Unicode obfuscation that regex-based stripping cannot reliably catch.
"""

import html
import bleach
from backend.config import MAX_USER_INPUT_LENGTH

MAX_INPUT_LENGTH: int = MAX_USER_INPUT_LENGTH


class ValidationError(ValueError):
    """Raised when user input validation fails."""
    pass


def sanitize_and_validate_input(text: str) -> str:
    """Sanitizes user input and enforces length limits.

    Removes all HTML tags, whitespace, and validates the length limits. Defeats
    double-encoding bypasses (e.g., <<script>script>) by using a two-pass
    unescape and clean filter via bleach.

    Args:
        text: Raw untrusted user input string.

    Returns:
        The sanitized string.

    Raises:
        ValidationError: If input is empty, too long, or contains only blank tags.
    """
    if not text:
        raise ValidationError("Input content cannot be empty.")

    sanitized: str = text.strip()

    # Enforce length cap BEFORE stripping so an attacker cannot pad with tags
    # to sneak past the limit after stripping removes them.
    if len(sanitized) > MAX_INPUT_LENGTH:
        raise ValidationError(
            f"Input is too long. Maximum allowed length is {MAX_INPUT_LENGTH} characters."
        )

    # First pass: strip HTML tags (bleach removes tags, HTML-encodes remaining special chars)
    sanitized = bleach.clean(sanitized, tags=[], attributes={}, strip=True)

    # Second pass: unescape any HTML entities that survived, then strip again.
    # This defeats the double-encoding bypass: <<script>script>alert(1)</script>/script>
    # After first pass bleach produces &lt;script&gt;alert(1)... — unescape recovers
    # the raw <script> tag; the second bleach pass then removes it.
    sanitized = bleach.clean(html.unescape(sanitized), tags=[], attributes={}, strip=True)

    # Reject if stripping HTML left nothing
    if not sanitized.strip():
        raise ValidationError("Input contains invalid or empty characters.")

    return sanitized.strip()
