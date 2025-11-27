def caesar_encrypt(text, shift):
    """Encrypts text using Caesar Cipher."""
    result = ""
    for char in text:
        if char.isalpha():
            ascii_offset = 65 if char.isupper() else 97
            # (char_code - offset + shift) % 26 + offset
            result += chr((ord(char) - ascii_offset + shift) % 26 + ascii_offset)
        else:
            result += char
    return result

def caesar_decrypt(text, shift):
    """Decrypts text using Caesar Cipher."""
    # Decryption is just encryption with negative shift
    return caesar_encrypt(text, -shift)
