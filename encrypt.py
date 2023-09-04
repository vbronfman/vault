import hvac
import base64


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
plaintext="my secret data"

# convert to base64
plaintext64 = base64.b64encode(plaintext.encode()).decode()

# the name of the key to use for encryption
name='my-key'
data = {'plaintext': plaintext64}
response = client.secrets.transit.encrypt_data(name=name,**data)

#print (f"response {response['data']['ciphertext']}")
print (response['data']['ciphertext'])
