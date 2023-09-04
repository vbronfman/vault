# there is example https://developer.hashicorp.com/vault/tutorials/kubernetes/kubernetes-sidecar 

Hashicorp Vault implementation and usage
https://youtu.be/q3Rrup48zlM?si=BGtLpzj8sVcXCkRn

Vault set up in Kubernetes

sudo helm repo add hashicorp https://helm.releases.hashicorp.com
sudo helm repo update
sudo helm search repo hashicorp/vault

5. Create config for helm chart:
nano ~/Develop/helm-vault-raft-values.yml
ana@ana-RD510-S-AD34E:~/Develop/Vault$ cat helm-vault-raft-values.yml
server:
  affinity: ""
  ha:
    enabled: true
    raft:
      enabled: true
  ui:
    enabled: true
    serviceType: "NodePort"
  injector:
    enabled: true

6. Create namespace vault
kubectl create ns vault

7. Install helm chart with values from config:
sudo helm install vault hashicorp/vault --values  ~/Develop/helm-vault-raft-values.yml -n vault

sudo helm status vault

8. Init Vault cluster. Pay attention there is 3 pods of Vault has been created due to 'ha' set 'true'
 907  kubectl exec vault-0 -- vault operator init --key-shares=1 --key-threshold=1 --format=json > cluster-keys.json
  908  cat cluster-keys.json 
  909  VAULT_UNSEAL_KEY=n1FWw6BAb5feSOC3fOSIHc0We8dsO/hyRs9go3brk+0=
  911  kubectl exec vault-0 -- vault operator unseal $VAULT_UNSEAL_KEY
  912  kubectl exec -ti vault-1 -- vault operator raft join http://vault-0.vault-internal:8200  
  913  kubectl exec -ti vault-2 -- vault operator raft join http://vault-0.vault-internal:8200  
  914  kubectl get pod
  915  kubectl exec vault-1 -- vault operator unseal $VAULT_UNSEAL_KEY
  917  kubectl port-forward vault-0 8200:8200
  918  cat cluster-keys.json 
{
  "unseal_keys_b64": [
    "n1FWw6BAb5feSOC3fOSIHc0We8dsO/hyRs9go3brk+0="
  ],
  "unseal_keys_hex": [
    "9f5156c3a0406f97de48e0b77ce4881dcd167bc76c3bf87246cf60a376eb93ed"
  ],
  "unseal_shares": 1,
  "unseal_threshold": 1,
  "recovery_keys_b64": [],
  "recovery_keys_hex": [],
  "recovery_keys_shares": 0,
  "recovery_keys_threshold": 0,
  "root_token": "hvs.dpUcIk4eJ2ZaXfiyuy4qu5v4"
}

9. Login UI localhost:8200 with token
Use value of "unseal_keys_b64" 

10. login to vault from within pod:
kubectl exec -it vault-0 -- /bin/sh 
vault login 
Feed "root_token" value from cluster-keys.json  


    Retrieve secrets with Approle 

14. Enable secret engine:
vault secrets enable -path=secret kv-v2

15. Create secret vault kv put secret/helloworld username=cyberships password=shyboy123

15. Read secret 
vault kv get secret/helloworld
===== Secret Path =====
secret/data/helloworld

======= Metadata =======
Key                Value
---                -----
created_time       2023-09-01T18:39:18.810533555Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1

====== Data ======
Key         Value
---         -----
password    shyboy123
username    cyberships



16. create file (policy) what allows read every secret:
cat <<EOF > /home/vault/app-policy.hcl
   path "secret*" {
     capabilities = ["read"]
   }
EOF
17. Write policy into Vault, the name is 'app'  
 vault policy write app /home/vault/app-policy.hcl

18. Create auth method known as approle so we can actuaally go and retrieve secrets 

 vault auth enable approle
19. Create approle called "app" with policy "app"
 vault write auth/approle/role/app policies=app
20. Read vaule of id to use for retrieve secret:
   vault read auth/approle/role/app/role-id
Key        Value
---        -----
role_id    d7ea626f-0cdc-9c76-92bf-5adcfabd0eea

Save the value for later use.

21. To get correspond secret for the role 
  vault write -f auth/approle/role/app/secret-id
Key                   Value
---                   -----
secret_id             c86ab179-b8fb-6607-6a11-060f42341901
secret_id_accessor    d20b8533-2e2c-2b1a-7e4f-671314d46854
secret_id_num_uses    0
secret_id_ttl         0s

22. Check in what the secret engine is created and within it there is creds of helloworld 
http://localhost:8200/ui/vault/secrets/secret/show/helloworld
and there is policy "app" created
and authentication method "approle" is enabled

23. We are going to create application to retrive creds
say Python. it requires module hvac 

Created appsapp.py

23.
         Retrieve secrets with Kubernetes

11.Enable kuberntes for Vault
   enter any  pod and enable 
kubectl exec -ti vault-0 -- /bin/sh
 vault auth enable kubernetes


12.
vault write auth/kubernetes/config \
token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
kubernetes_host=https://${KUBERNETES_PORT_443_TCP_ADDR}:443 \
kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt


23. Create role called "myapp" . it will use kubernetes service account "app" which will be later created in deployment manifest. Role
binded to namespace "demo". To this role attached policy 'app' which allows read secrets :

 vault write auth/kubernetes/role/myapp \
   bound_service_account_names=app \
   bound_service_account_namespaces=demo \
   policies=app \
   ttl=1h
This is pretty much all required to set kubernetes auth type on Vault

24. Next steps done in kubernetes deployment.

25. Create simple Flask app

26. Create manifest with annotations

27. Create 'demo' namespace as we set it somewhere previously
kubectl create ns demo


Vault encryption services

28. Enable transit engine: either in UI or 
kubectl exec -it vault-0 -n vault -- /bin/sh
vault secrets enable transit
29. Create secret key to use for encription
vault write -f transit/keys/my-key

30. Modify policy of previously created 'app'. In UI http://localhost:8200/ui/vault/policy/acl/app add : 
path "transit/encrypt/my-key" {
  capabilities = ["create","update"]
}

path "transit/decrypt/my-key" {
  capabilities = ["create","read","update"]
}

It grants approle encrypt and decrypt with key my-key

31. create script

ana@ana-RD510-S-AD34E:~/Develop/Vault$ cat decrypt.py 
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
