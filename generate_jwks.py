import json
import base64
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def int_to_base64url(value):
    """Converts an integer to a Base64URL-encoded string."""
    value_hex = format(value, 'x')
    # Ensure even length
    if len(value_hex) % 2 == 1:
        value_hex = '0' + value_hex
    value_bytes = bytes.fromhex(value_hex)
    return base64.urlsafe_b64encode(value_bytes).rstrip(b'=').decode('utf-8')

def generate_jwks(public_key_path="publickey.pem", output_path="jwks.json"):
    print(f"Reading public key from {public_key_path}...")
    try:
        with open(public_key_path, "rb") as key_file:
            public_key_data = key_file.read()
    except FileNotFoundError:
        print(f"Error: Could not find {public_key_path}. Did you generate it using openssl?")
        return

    # Load the public key
    try:
        # First try loading it as an X.509 Certificate
        from cryptography import x509
        cert = x509.load_pem_x509_certificate(public_key_data, default_backend())
        public_key = cert.public_key()
    except ValueError:
        # If it's not a cert, try loading it directly as a public key
        try:
            public_key = serialization.load_pem_public_key(
                public_key_data,
                backend=default_backend()
            )
        except Exception as e:
            print(f"Error loading public key: {e}")
            return

    # Extract public numbers (RSA specific)
    public_numbers = public_key.public_numbers()

    n_b64 = int_to_base64url(public_numbers.n)
    e_b64 = int_to_base64url(public_numbers.e)

    # Construct the JWKS dictionary
    jwk = {
        "kty": "RSA",
        "alg": "RS384",
        "use": "sig",
        # This kid MUST match the kid used in the JWT header in app.py
        "kid": "epic-demo-key",
        "n": n_b64,
        "e": e_b64
    }

    jwks = {
        "keys": [jwk]
    }

    # Write to jwks.json
    print(f"Writing JWK Set to {output_path}...")
    with open(output_path, "w") as f:
        json.dump(jwks, f, indent=4)

    print("Success! Your JWKS is ready.")
    print("You must host this jwks.json file on a public HTTPS server and provide the URL to Epic.")

if __name__ == "__main__":
    generate_jwks()
