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

MAX_INPUT_LENGTH = 400


class ValidationError(ValueError):
    pass


def sanitize_and_validate_input(text: str) -> str:
    """
    Sanitize user input and enforce length limits.

    Steps:
      1. Reject empty input.
      2. Strip leading/trailing whitespace.
      3. Enforce MAX_INPUT_LENGTH character cap.
      4. Strip ALL HTML tags using bleach (allowlist = empty → no tags permitted).
         bleach with strip=True removes tags; remaining text is HTML-entity-encoded.
      5. Unescape HTML entities (e.g. &amp;lt; → <) then run bleach a second time
         to catch any tags that were hidden behind entity encoding.
      6. Reject input that is blank after stripping.

    Returns the sanitized string, or raises ValidationError.
    """
    if not text:
        raise ValidationError("Input content cannot be empty.")

    # Strip whitespace
    sanitized = text.strip()

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
