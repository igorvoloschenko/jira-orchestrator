
class Secret:
    def Read(self) -> dict:
        """
        Read secret data from vault
        Format out data: {"secret":{"secret_name": "secret_data", ...}}
        """
        return {"secret":{}}


class File(Secret):
    def __init__(self, path: str):
        self.path = path
    
    def Read(self) -> dict:
        """
        Read secret data from yaml file
        Format out data: {"secret":{"secret_name": "secret_data", ...}}
        """
        import yaml

        data = open(self.path, "r").read()

        return {"secret": yaml.load(data)}


class Vault(Secret):
    def __init__(self, client: dict, auth: dict, secret_path: dict):
        import hvac

        self.secret_path = secret_path
        self.client = hvac.Client(**client)

        auth_type = auth.get("type")
        
        if auth_type == "kubernetes":
            role = auth["kubernetes"]["role"]
            jwt = open("/var/run/secrets/kubernetes.io/serviceaccount/token", mode="r").read()
            self.client.auth_kubernetes(role, jwt)

        elif auth_type == "token":
            self.client.token = auth.get("token")

    def Read(self) -> dict:
        """
        Read secret data from vault
        Format out data: {"secret":{"secret_name": "secret_data", ...}}
        """
        secrets = self.client.secrets
        return {"secret": secrets.kv.v1.read_secret(**self.secret_path)["data"]}


def ProviderNew(cfg) -> Secret:
    map_provider = {
            "vault": Vault 
        }
    provider_name = cfg.get("provider")
    
    if not provider_name:
        return Secret()
    
    return map_provider[provider_name](**cfg[provider_name])
