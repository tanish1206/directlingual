import re

MAX_INPUT_LENGTH = 400

class ValidationError(ValueError):
    pass

def sanitize_and_validate_input(text: str) -> str:
    """
    Sanitizes user input by removing HTML tags, whitespace, and validating length limits.
    """
    if not text:
        raise ValidationError("Input content cannot be empty.")
    
    # Strip whitespace
    sanitized = text.strip()
    
    # Validate length
    if len(sanitized) > MAX_INPUT_LENGTH:
        raise ValidationError(f"Input is too long. Maximum allowed length is {MAX_INPUT_LENGTH} characters.")
    
    # Strip script blocks and their content
    sanitized = re.sub(r'<script.*?>.*?</script>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    # Strip HTML tags
    sanitized = re.sub(r'<[^>]*>', '', sanitized)
    
    # Disallow completely non-printable/gibberish blank input
    if not sanitized:
        raise ValidationError("Input contains invalid or empty characters.")
        
    return sanitized
