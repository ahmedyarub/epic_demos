# Epic on FHIR Backend Service Demo

This is a simple Python CLI application demonstrating how to connect to the [Epic on FHIR](https://fhir.epic.com/) sandbox using a **Backend System** (system-to-system) approach via the **Client Credentials** OAuth 2.0 flow.

The application reads an Epic App Client ID and a private key, generates a signed JWT, exchanges it for an OAuth 2.0 access token, and fetches patient demographics from the FHIR R4 API.

## 1. Create an Epic on FHIR Account

1. Go to [fhir.epic.com](https://fhir.epic.com/) and click on **Build Apps**.
2. If you don't already have an account, sign up for a free developer account.
3. Once logged in, you will have access to the developer portal to manage your applications.

## 2. Generate Asymmetric Keys

Epic requires asymmetric authentication (a public/private key pair) for Backend Systems. You will sign a JWT with the private key, and Epic will verify it with the public key you provide them.

Run the following OpenSSL commands in the terminal (in the root directory of this project) to generate the keys:

```bash
# 1. Generate a 2048-bit RSA private key
openssl genrsa -out privatekey.pem 2048

# 2. Generate the corresponding public key in X.509 certificate format (PEM)
openssl req -new -x509 -key privatekey.pem -out publickey.pem -days 365 -subj '/CN=my-epic-demo-app'
```

Keep your `privatekey.pem` secure and never commit it to source control!

## 3. Generate and Host JWK Set (JWKS)

Epic now requires Backend OAuth 2.0 apps to host their public keys at a JWK Set URL (JKU) rather than uploading a static key.

1. Install the required Python dependencies to use the JWKS generator script:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. Run the provided script to generate your `jwks.json` from the public key:
   ```bash
   python3 generate_jwks.py
   ```
   This script will read `publickey.pem` and output a `jwks.json` file. It sets the `kid` (Key ID) to `epic-demo-key`, which matches the `kid` used when generating the JWT in `app.py`.

3. **Host the JWKS File:** You must host this `jwks.json` file on a public HTTPS server. Common free options include GitHub Pages, AWS S3, or standard web hosting. Note the public URL (e.g., `https://my-domain.com/jwks.json`).

## 4. Create an App in Epic on FHIR

1. Log in to [fhir.epic.com](https://fhir.epic.com/).
2. Navigate to **Build Apps** -> **Create**.
3. Fill out the application details:
   - **App Name**: e.g., "Python Backend Demo"
   - **Primary User Type**: Select **Backend Systems** (since this is a system-to-system integration without user intervention).
   - **Incoming APIs**: Select the APIs you need, for example, `Patient.Read (R4)`.
   - **App FHIR Version**: Select `R4`.
   - **Is this app a confidential client?**: Check this box.
4. Click **Save** and then **Ready for Production** (or Ready for Sandbox).
5. Note down the **Non-Production Client ID** provided by Epic. You will need this for the configuration.
6. Now you need to upload your JWKS URL. On the Build Apps page, select **Review and Manage Downloads** for your new application.
7. Select the **Non-Production** environment type.
8. In the **JWK Set URL** section, un-check "Use app-level JWK Set URL", and provide the public URL where you hosted your `jwks.json` file.
9. Click **Activate**.

## 5. Application Configuration

Create a `.env` file in the root directory and add your Client ID:
```env
# Your Epic App's Client ID (from fhir.epic.com)
EPIC_CLIENT_ID=your_client_id_here

# Path to your generated private key (default is privatekey.pem in the same folder)
PRIVATE_KEY_PATH=privatekey.pem

# Optional: A specific sandbox patient ID to test with
TEST_PATIENT_ID=erXuFYUfucBZaryVksYEcMg3
```

## 6. Running and Testing the App

Once configured, simply run the Python script:

```bash
python3 app.py
```

### Expected Output
If the configuration is correct, the script will:
1. Generate and sign a JWT using your private key.
2. Send the JWT to the Epic Token Endpoint (`https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token`).
3. Receive a bearer access token.
4. Use the access token to call the FHIR R4 Patient endpoint.
5. Print a summary of the patient's demographics.

Example output:
```text
Generating signed JWT...
Requesting access token from https://fhir.epic.com/interconnect-fhir-oauth/oauth2/token...
Successfully obtained access token!
Fetching Patient/erXuFYUfucBZaryVksYEcMg3 from https://fhir.epic.com/interconnect-fhir-oauth/api/FHIR/R4/Patient/erXuFYUfucBZaryVksYEcMg3...
Successfully fetched patient data!

--- Patient Demographics ---
ID: erXuFYUfucBZaryVksYEcMg3
Name: Jason Argonaut
Gender: male
Birth Date: 1985-08-01
----------------------------
```
