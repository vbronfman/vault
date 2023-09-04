import hvac

client = hvac.Client(url='http://localhost:8200')

response = client.auth.approle.login(
   role_id="d7ea626f-0cdc-9c76-92bf-5adcfabd0eea", # vault read auth/approle/role/app/role-id
   secret_id="c86ab179-b8fb-6607-6a11-060f42341901"  # vault write -f auth/approle/role/app/secret-id
)

client_token = response['auth']['client_token']

client_authenticated = hvac.Client( url='http://localhost:8200',
                                   token = client_token )

response = client_authenticated.secrets.kv.v2.read_secret_version(
   mount_point="secret",
   path = "helloworld",
   raise_on_deleted_version = True
)

secret_data = response['data']['data']

print(f"Username: {secret_data['username']}")
print(f"Pass: {secret_data['password']}")
