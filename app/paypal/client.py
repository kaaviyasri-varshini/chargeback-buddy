"""PayPal API client for sandbox testing."""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class PayPalClient:
    """Async PayPal API client with OAuth2 authentication."""
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize PayPal client.
        
        Args:
            client_id: PayPal client ID (defaults to settings)
            client_secret: PayPal client secret (defaults to settings)
            base_url: PayPal API base URL (defaults to settings sandbox URL)
        """
        self.client_id = client_id or settings.paypal_client_id
        self.client_secret = client_secret or settings.paypal_client_secret
        self.base_url = base_url or settings.paypal_base_url
        
        if not self.client_id or not self.client_secret:
            raise ValueError("PayPal credentials must be set")
        
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[datetime] = None
        self._http_client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close the HTTP client."""
        await self._http_client.aclose()
    
    async def __aenter__(self):
        """Context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.close()
    
    async def _get_access_token(self) -> str:
        """
        Get or refresh OAuth2 access token.
        
        Returns:
            Access token string
        """
        # Check if we have a valid cached token
        if self._access_token and self._token_expires_at:
            if datetime.utcnow() < self._token_expires_at:
                return self._access_token
        
        # Request new token
        logger.info("Requesting new PayPal access token...")
        
        url = f"{self.base_url}/v1/oauth2/token"
        headers = {
            "Accept": "application/json",
            "Accept-Language": "en_US",
        }
        data = {
            "grant_type": "client_credentials"
        }
        
        try:
            response = await self._http_client.post(
                url,
                auth=(self.client_id, self.client_secret),
                headers=headers,
                data=data
            )
            response.raise_for_status()
            
            token_data = response.json()
            self._access_token = token_data["access_token"]
            
            # Cache token with 5-minute buffer before expiry
            expires_in = token_data.get("expires_in", 3600)
            self._token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 300)
            
            logger.info("Successfully obtained PayPal access token")
            return self._access_token
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get PayPal access token: {e.response.status_code}")
            logger.error(f"Response: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error getting PayPal access token: {e}")
            raise
    
    async def _make_request(
        self,
        method: str,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an authenticated API request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path (e.g., /v1/customer/disputes/{dispute_id})
            json_data: JSON body data
            params: Query parameters
            
        Returns:
            Response JSON
        """
        token = await self._get_access_token()
        
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        try:
            response = await self._http_client.request(
                method,
                url,
                headers=headers,
                json=json_data,
                params=params
            )
            response.raise_for_status()
            
            return response.json() if response.text else {}
            
        except httpx.HTTPStatusError as e:
            logger.error(f"PayPal API error: {e.response.status_code}")
            logger.error(f"Response: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error making PayPal API request: {e}")
            raise
    
    async def get_dispute(self, dispute_id: str) -> Dict[str, Any]:
        """
        Get dispute details.
        
        Args:
            dispute_id: PayPal dispute ID
            
        Returns:
            Dispute details dictionary
        """
        logger.info(f"Fetching dispute {dispute_id}...")
        return await self._make_request("GET", f"/v1/customer/disputes/{dispute_id}")
    
    async def provide_evidence(
        self,
        dispute_id: str,
        notes: Optional[str] = None,
        documents: Optional[list[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Provide evidence for a dispute.
        
        Args:
            dispute_id: PayPal dispute ID
            notes: Seller notes/comments
            documents: List of document references
            
        Returns:
            Response dictionary
        """
        logger.info(f"Providing evidence for dispute {dispute_id}...")
        
        evidence = {}
        if notes:
            evidence["notes"] = notes
        if documents:
            evidence["documents"] = documents
        
        return await self._make_request(
            "POST",
            f"/v1/customer/disputes/{dispute_id}/provide-evidence",
            json_data=evidence
        )
    
    async def verify_webhook_signature(
        self,
        webhook_id: str,
        headers: Dict[str, str],
        body: bytes
    ) -> bool:
        """
        Verify PayPal webhook signature.
        
        Args:
            webhook_id: PayPal webhook ID
            headers: Request headers containing signature data
            body: Raw request body
            
        Returns:
            True if signature is valid
        """
        logger.info("Verifying webhook signature...")
        
        verification_data = {
            "auth_algo": headers.get("paypal-auth-algo"),
            "cert_url": headers.get("paypal-cert-url"),
            "transmission_id": headers.get("paypal-transmission-id"),
            "transmission_sig": headers.get("paypal-transmission-sig"),
            "transmission_time": headers.get("paypal-transmission-time"),
            "webhook_id": webhook_id,
            "webhook_event": body.decode("utf-8")
        }
        
        try:
            response = await self._make_request(
                "POST",
                "/v1/notifications/verify-webhook-signature",
                json_data=verification_data
            )
            
            verification_status = response.get("verification_status", "")
            is_valid = verification_status == "SUCCESS"
            
            logger.info(f"Webhook verification: {verification_status}")
            return is_valid
            
        except Exception as e:
            logger.error(f"Webhook verification failed: {e}")
            return False
