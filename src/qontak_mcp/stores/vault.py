"""
HashiCorp Vault token store for production environments.

This is the RECOMMENDED token store for PRODUCTION deployments.

Benefits of using Vault:
- Encryption at rest and in transit
- Comprehensive audit logging
- Fine-grained access control policies
- Dynamic secret generation
- Secret rotation and revocation
- Centralized secrets management
- Integration with identity providers

This store uses Vault's KV v2 secrets engine to store Qontak OAuth tokens
securely for multi-tenant deployments.
"""

import os
from typing import Optional, Any

from .base import TokenStore, TokenData


class VaultTokenStore(TokenStore):
    """
    HashiCorp Vault token store for production multi-tenant deployments.
    
    ✅ RECOMMENDED FOR PRODUCTION ✅
    
    This store provides enterprise-grade security for storing OAuth credentials:
    - Secrets are encrypted at rest using Vault's encryption
    - All access is logged for audit compliance
    - Access can be controlled via Vault policies
    - Supports secret versioning and rollback
    
    Configuration via environment variables:
    - VAULT_ADDR: Vault server address (required, e.g., https://vault.example.com:8200)
    - VAULT_TOKEN: Vault authentication token (required)
    - VAULT_MOUNT_PATH: KV v2 mount path (default: secret)
    - VAULT_SECRET_PATH: Base path for secrets (default: qontak/tokens)
    - VAULT_NAMESPACE: Vault namespace for enterprise (optional)
    
    Vault Setup Requirements:
    1. KV v2 secrets engine enabled at VAULT_MOUNT_PATH
    2. Policy granting read/write access to VAULT_SECRET_PATH/*
    3. Valid authentication token with the above policy
    
    Example Vault Policy:
    ```hcl
    path "secret/data/qontak/tokens/*" {
      capabilities = ["create", "read", "update", "delete", "list"]
    }
    path "secret/metadata/qontak/tokens/*" {
      capabilities = ["read", "delete", "list"]
    }
    ```
    """
    
    def __init__(
        self,
        vault_addr: Optional[str] = None,
        vault_token: Optional[str] = None,
        mount_path: Optional[str] = None,
        secret_path: Optional[str] = None,
        namespace: Optional[str] = None,
    ) -> None:
        """
        Initialize the Vault token store.
        
        Args:
            vault_addr: Vault server address. Falls back to VAULT_ADDR env var.
            vault_token: Vault auth token. Falls back to VAULT_TOKEN env var.
            mount_path: KV v2 mount path. Falls back to VAULT_MOUNT_PATH env var.
            secret_path: Base path for secrets. Falls back to VAULT_SECRET_PATH env var.
            namespace: Vault namespace (enterprise). Falls back to VAULT_NAMESPACE env var.
        
        Raises:
            ImportError: If hvac package is not installed
            ValueError: If required configuration is missing
        """
        try:
            import hvac
        except ImportError as e:
            raise ImportError(
                "Vault support is not installed. "
                "Install with: pip install 'qontak-mcp[vault]'"
            ) from e
        
        self._vault_addr = vault_addr or os.getenv("VAULT_ADDR")
        self._vault_token = vault_token or os.getenv("VAULT_TOKEN")
        self._mount_path = mount_path or os.getenv("VAULT_MOUNT_PATH", "secret")
        self._secret_path = secret_path or os.getenv("VAULT_SECRET_PATH", "qontak/tokens")
        self._namespace = namespace or os.getenv("VAULT_NAMESPACE")
        
        if not self._vault_addr:
            raise ValueError(
                "Vault address is required. "
                "Set VAULT_ADDR environment variable or pass vault_addr parameter."
            )
        
        if not self._vault_token:
            raise ValueError(
                "Vault token is required. "
                "Set VAULT_TOKEN environment variable or pass vault_token parameter."
            )
        
        # Create Vault client
        self._client = hvac.Client(
            url=self._vault_addr,
            token=self._vault_token,
            namespace=self._namespace,
        )
        
        # Verify connection
        if not self._client.is_authenticated():
            raise ValueError(
                "Failed to authenticate with Vault. "
                "Please check your VAULT_TOKEN is valid."
            )
    
    def _get_secret_path(self, user_id: Optional[str]) -> str:
        """Get the full secret path for a user's tokens."""
        user_key = user_id if user_id else "_default"
        return f"{self._secret_path}/{user_key}"
    
    def get(self, user_id: Optional[str] = None) -> Optional[TokenData]:
        """
        Retrieve token data from Vault.
        
        Args:
            user_id: User/tenant identifier. Uses "_default" if not provided.
        
        Returns:
            TokenData if found, None otherwise
        """
        path = self._get_secret_path(user_id)
        
        try:
            response = self._client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point=self._mount_path,
                raise_on_deleted_version=True,
            )
            
            if response is None:
                return None
            
            data = response.get("data", {}).get("data", {})
            if not data or "refresh_token" not in data:
                return None
            
            return TokenData(
                refresh_token=data["refresh_token"],
                access_token=data.get("access_token"),
                expires_at=data.get("expires_at"),
            )
        except Exception:
            # Secret doesn't exist or other error
            return None
    
    def save(self, token_data: TokenData, user_id: Optional[str] = None) -> None:
        """
        Save token data to Vault.
        
        Args:
            token_data: Token data to save
            user_id: User/tenant identifier. Uses "_default" if not provided.
        """
        path = self._get_secret_path(user_id)
        
        secret_data: dict[str, Any] = {
            "refresh_token": token_data.refresh_token,
        }
        
        if token_data.access_token:
            secret_data["access_token"] = token_data.access_token
        if token_data.expires_at:
            secret_data["expires_at"] = token_data.expires_at
        
        self._client.secrets.kv.v2.create_or_update_secret(
            path=path,
            secret=secret_data,
            mount_point=self._mount_path,
        )
    
    def delete(self, user_id: Optional[str] = None) -> bool:
        """
        Delete token data from Vault.
        
        This performs a soft delete (marks as deleted but keeps history).
        Use destroy() for permanent deletion.
        
        Args:
            user_id: User/tenant identifier. Uses "_default" if not provided.
        
        Returns:
            True if deletion was attempted (doesn't guarantee secret existed)
        """
        path = self._get_secret_path(user_id)
        
        try:
            self._client.secrets.kv.v2.delete_latest_version_of_secret(
                path=path,
                mount_point=self._mount_path,
            )
            return True
        except Exception:
            return False
    
    def destroy(self, user_id: Optional[str] = None) -> bool:
        """
        Permanently destroy all versions of token data from Vault.
        
        WARNING: This permanently removes the secret and all its history.
        This action cannot be undone.
        
        Args:
            user_id: User/tenant identifier. Uses "_default" if not provided.
        
        Returns:
            True if destruction was attempted
        """
        path = self._get_secret_path(user_id)
        
        try:
            # Get metadata to find all versions
            metadata = self._client.secrets.kv.v2.read_secret_metadata(
                path=path,
                mount_point=self._mount_path,
            )
            
            if metadata:
                versions = list(metadata.get("data", {}).get("versions", {}).keys())
                if versions:
                    self._client.secrets.kv.v2.destroy_secret_versions(
                        path=path,
                        versions=versions,
                        mount_point=self._mount_path,
                    )
            return True
        except Exception:
            return False
    
    def exists(self, user_id: Optional[str] = None) -> bool:
        """
        Check if token data exists for a user.
        
        Args:
            user_id: User/tenant identifier. Uses "_default" if not provided.
        
        Returns:
            True if token data exists, False otherwise
        """
        return self.get(user_id) is not None
    
    def list_users(self) -> list[str]:
        """
        List all user IDs that have stored tokens.
        
        Returns:
            List of user IDs with stored tokens
        """
        try:
            response = self._client.secrets.kv.v2.list_secrets(
                path=self._secret_path,
                mount_point=self._mount_path,
            )
            
            if response is None:
                return []
            
            keys = response.get("data", {}).get("keys", [])
            # Remove trailing slashes from directory entries
            return [k.rstrip("/") for k in keys]
        except Exception:
            return []
