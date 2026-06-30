"""Chargement de la configuration depuis le fichier .env."""
import os
from dotenv import load_dotenv

load_dotenv()


def _get(name: str, default: str = "") -> str:
    return (os.getenv(name) or default).strip()


class Settings:
    # Azure AD
    tenant_id = _get("AZURE_TENANT_ID")
    client_id = _get("AZURE_CLIENT_ID")
    client_secret = _get("AZURE_CLIENT_SECRET")

    # SharePoint
    hostname = _get("SHAREPOINT_HOSTNAME")
    site_path = _get("SHAREPOINT_SITE_PATH")
    list_name = _get("SHAREPOINT_LIST_NAME", "Suivi Materiel")

    # Application
    app_password = _get("APP_PASSWORD")

    @property
    def configured(self) -> bool:
        return all([self.tenant_id, self.client_id, self.client_secret, self.hostname])

    def missing(self) -> list[str]:
        req = {
            "AZURE_TENANT_ID": self.tenant_id,
            "AZURE_CLIENT_ID": self.client_id,
            "AZURE_CLIENT_SECRET": self.client_secret,
            "SHAREPOINT_HOSTNAME": self.hostname,
        }
        return [k for k, v in req.items() if not v]


settings = Settings()
