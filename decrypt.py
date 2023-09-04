import hvac
import base64
import sys

client = hvac.Client(url='http://localhost:8200')

#Login to Vault
response = client.auth.approle.login(
   role_id="d7ea626f-0cdc-9c76-92bf-5adcfabd0eea", # vault read auth/approle/role/app/role-id
   secret_id="c86ab179-b8fb-6607-6a11-060f42341901"  # vault write -f auth/approle/role/app/secret-id
)

client_token = response['auth']['client_token']

client_authenticated = hvac.Client( url='http://localhost:8200',
                                   token = client_token )

# Encrypt simple string
# 
ciphertext=sys.argv[1]

# the name of the key to use for encryption
name='my-key'

response = client.secrets.transit.decrypt_data(name=name,ciphertext=ciphertext)

plaintext=base64.b64decode(response['data']['plaintext']).decode()

print (f"decoded text {plaintext}")
