import os
import uuid
import time
import requests
import jwt
from dotenv import load_dotenv

load_dotenv()

# Configuration
# Epic FHIR Sandbox token endpoint
TOKEN_ENDPOINT = "https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token"
# Epic FHIR Sandbox base URL (R4)
FHIR_BASE_URL = "https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4"

def load_private_key(filepath):
    with open(filepath, 'r') as f:
        return f.read()

def generate_jwt(client_id, private_key):
    """Generates the signed JWT for authentication."""
    # Note: When using a JWKS URL, the authorization server may require a Key ID (kid)
    # to identify which key in the JWKS to use for verification.
    # For this demo, we'll use a static kid 'epic-demo-key'.
    # Ensure this matches the 'kid' in your generated jwks.json!
    headers = {
        "alg": "RS384",
        "typ": "JWT",
        "kid": "epic-demo-key"
    }

    now = int(time.time())
    payload = {
        "iss": client_id,
        "sub": client_id,
        "aud": TOKEN_ENDPOINT,
        "jti": str(uuid.uuid4()),
        "exp": now + 300, # Max 5 minutes (300 seconds)
        "nbf": now,
        "iat": now
    }

    encoded_jwt = jwt.encode(payload, private_key, algorithm="RS384", headers=headers)
    return encoded_jwt

def get_access_token(client_id, encoded_jwt):
    """Exchanges the JWT for an access token."""
    data = {
        "grant_type": "client_credentials",
        "client_assertion_type": "urn:ietf:params:oauth:client-assertion-type:jwt-bearer",
        "client_assertion": encoded_jwt
    }

    print(f"Requesting access token from {TOKEN_ENDPOINT}...")
    response = requests.post(TOKEN_ENDPOINT, data=data)

    if response.status_code == 200:
        print("Successfully obtained access token!")
        return response.json().get("access_token")
    else:
        print(f"Failed to get access token. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def fetch_patient_demographics(access_token, patient_id):
    """Fetches patient demographics using the access token."""
    url = f"{FHIR_BASE_URL}/Patient/{patient_id}"

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }

    print(f"Fetching Patient/{patient_id} from {url}...")
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        print("Successfully fetched patient data!")
        return response.json()
    else:
        print(f"Failed to fetch patient data. Status code: {response.status_code}")
        print(f"Response: {response.text}")
        return None

def main():
    client_id = os.getenv("EPIC_CLIENT_ID")
    private_key_path = os.getenv("PRIVATE_KEY_PATH", "privatekey.pem")

    # A known sandbox test patient ID from Epic's documentation
    # erXuFYUfucBZaryVksYEcMg3 is frequently used as a test patient, e.g. for Jason Argonaut
    test_patient_id = os.getenv("TEST_PATIENT_ID", "erXuFYUfucBZaryVksYEcMg3")

    if not client_id:
        print("Error: EPIC_CLIENT_ID environment variable not set.")
        print("Please check your .env file.")
        return

    try:
        private_key = load_private_key(private_key_path)
    except FileNotFoundError:
        print(f"Error: Private key file not found at {private_key_path}.")
        print("Did you generate it using the instructions in the README?")
        return

    # 1. Generate JWT
    print("Generating signed JWT...")
    signed_jwt = generate_jwt(client_id, private_key)

    # 2. Get Access Token
    access_token = get_access_token(client_id, signed_jwt)

    if not access_token:
        return

    # 3. Fetch Data
    patient_data = fetch_patient_demographics(access_token, test_patient_id)

    if patient_data:
        # Print a simple summary
        name = patient_data.get('name', [{}])[0]
        given_names = " ".join(name.get('given', []))
        family_name = name.get('family', 'Unknown')

        print("\n--- Patient Demographics ---")
        print(f"ID: {patient_data.get('id')}")
        print(f"Name: {given_names} {family_name}")
        print(f"Gender: {patient_data.get('gender')}")
        print(f"Birth Date: {patient_data.get('birthDate')}")
        print("----------------------------\n")

if __name__ == "__main__":
    main()
