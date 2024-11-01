import secrets
import string

def rnd_id(length=8) -> str:
    """
    Generates a random alphanumeric string of the specified length.

    Args:
        length (int): The length of the generated string. Defaults to 8.

    Returns:
        str: A random alphanumeric string.
    """
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))
