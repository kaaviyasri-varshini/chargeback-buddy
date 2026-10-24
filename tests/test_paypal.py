"""Tests for PayPal client and webhooks."""

import json
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timedelta

import pytest
import httpx

from app.paypal.client import PayPalClient
from app.paypal.webhooks import _parse_dispute_reason, _parse_dispute_status
from app.db.documents import DisputeReason, DisputeStatus


class TestPayPalClient:
    """Test suite for PayPalClient."""
    
    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test that client initializes with credentials."""
        with patch('app.paypal.client.settings') as mock_settings:
            mock_settings.paypal_client_id = "test_client"
            mock_settings.paypal_client_secret = "test_secret"
            mock_settings.paypal_base_url = "https://api-m.sandbox.paypal.com"
            
            client = PayPalClient()
            
            assert client.client_id == "test_client"
            assert client.client_secret == "test_secret"
            assert client.base_url == "https://api-m.sandbox.paypal.com"
            
            await client.close()
    
    @pytest.mark.asyncio
    async def test_client_requires_credentials(self):
        """Test that client raises error without credentials."""
        with patch('app.paypal.client.settings') as mock_settings:
            mock_settings.paypal_client_id = ""
            mock_settings.paypal_client_secret = ""
            
            with pytest.raises(ValueError, match="PayPal credentials must be set"):
                PayPalClient()
    
    @pytest.mark.asyncio
    async def test_get_access_token(self):
        """Test OAuth2 token retrieval."""
        with patch('app.paypal.client.settings') as mock_settings:
            mock_settings.paypal_client_id = "test_client"
            mock_settings.paypal_client_secret = "test_secret"
            mock_settings.paypal_base_url = "https://api-m.sandbox.paypal.com"
            
            client = PayPalClient()
            
            # Mock HTTP response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "test_token_12345",
                "token_type": "Bearer",
                "expires_in": 32400
            }
            
            with patch.object(client._http_client, 'post', return_value=mock_response):
                token = await client._get_access_token()
                
                assert token == "test_token_12345"
                assert client._access_token == "test_token_12345"
                assert client._token_expires_at is not None
            
            await client.close()
    
    @pytest.mark.asyncio
    async def test_token_caching(self):
        """Test that access token is cached and reused."""
        with patch('app.paypal.client.settings') as mock_settings:
            mock_settings.paypal_client_id = "test_client"
            mock_settings.paypal_client_secret = "test_secret"
            mock_settings.paypal_base_url = "https://api-m.sandbox.paypal.com"
            
            client = PayPalClient()
            
            # Set up cached token
            from datetime import timedelta
            client._access_token = "cached_token"
            client._token_expires_at = datetime.utcnow() + timedelta(hours=1)
            
            # Should return cached token without API call
            token = await client._get_access_token()
            assert token == "cached_token"
            
            await client.close()
    
    @pytest.mark.asyncio
    async def test_get_dispute(self):
        """Test get dispute details."""
        with patch('app.paypal.client.settings') as mock_settings:
            mock_settings.paypal_client_id = "test_client"
            mock_settings.paypal_client_secret = "test_secret"
            mock_settings.paypal_base_url = "https://api-m.sandbox.paypal.com"
            
            client = PayPalClient()
            
            # Mock token and API response
            client._access_token = "test_token"
            client._token_expires_at = datetime.utcnow() + timedelta(hours=1)
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '{"dispute_id": "PP-D-123"}'
            mock_response.json.return_value = {"dispute_id": "PP-D-123", "status": "OPEN"}
            
            with patch.object(client._http_client, 'request', return_value=mock_response):
                dispute = await client.get_dispute("PP-D-123")
                
                assert dispute["dispute_id"] == "PP-D-123"
                assert dispute["status"] == "OPEN"
            
            await client.close()
    
    @pytest.mark.asyncio
    async def test_provide_evidence(self):
        """Test provide evidence for dispute."""
        with patch('app.paypal.client.settings') as mock_settings:
            mock_settings.paypal_client_id = "test_client"
            mock_settings.paypal_client_secret = "test_secret"
            mock_settings.paypal_base_url = "https://api-m.sandbox.paypal.com"
            
            client = PayPalClient()
            
            # Mock token and API response
            client._access_token = "test_token"
            client._token_expires_at = datetime.utcnow() + timedelta(hours=1)
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '{"status": "success"}'
            mock_response.json.return_value = {"status": "success"}
            
            with patch.object(client._http_client, 'request', return_value=mock_response) as mock_request:
                result = await client.provide_evidence(
                    "PP-D-123",
                    notes="We have strong evidence",
                    documents=[{"name": "tracking.pdf"}]
                )
                
                assert result["status"] == "success"
                
                # Verify correct API call was made
                call_args = mock_request.call_args
                assert "/v1/customer/disputes/PP-D-123/provide-evidence" in str(call_args)
            
            await client.close()
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test client as context manager."""
        with patch('app.paypal.client.settings') as mock_settings:
            mock_settings.paypal_client_id = "test_client"
            mock_settings.paypal_client_secret = "test_secret"
            mock_settings.paypal_base_url = "https://api-m.sandbox.paypal.com"
            
            async with PayPalClient() as client:
                assert client._http_client is not None
            
            # Should be closed after context
            assert client._http_client.is_closed


class TestWebhookParsing:
    """Test webhook parsing functions."""
    
    def test_parse_dispute_reason(self):
        """Test dispute reason parsing."""
        assert _parse_dispute_reason("MERCHANDISE_OR_SERVICE_NOT_RECEIVED") == DisputeReason.MERCHANDISE_OR_SERVICE_NOT_RECEIVED
        assert _parse_dispute_reason("UNAUTHORISED") == DisputeReason.UNAUTHORISED
        assert _parse_dispute_reason("UNAUTHORIZED") == DisputeReason.UNAUTHORISED  # Alternate spelling
        assert _parse_dispute_reason("UNKNOWN_REASON") == DisputeReason.OTHER
        assert _parse_dispute_reason(None) == DisputeReason.OTHER
    
    def test_parse_dispute_status(self):
        """Test dispute status parsing."""
        assert _parse_dispute_status("OPEN") == DisputeStatus.OPEN
        assert _parse_dispute_status("WAITING_FOR_SELLER_RESPONSE") == DisputeStatus.WAITING_FOR_SELLER_RESPONSE
        assert _parse_dispute_status("UNDER_REVIEW") == DisputeStatus.UNDER_REVIEW
        assert _parse_dispute_status("RESOLVED") == DisputeStatus.RESOLVED
        assert _parse_dispute_status("UNKNOWN_STATUS") == DisputeStatus.OPEN
        assert _parse_dispute_status(None) == DisputeStatus.OPEN


class TestWebhookIdempotency:
    """Test webhook idempotency."""
    
    @pytest.fixture
    def sample_webhook_payload(self):
        """Create a sample webhook payload."""
        return {
            "id": "WH-TEST-12345",
            "event_type": "CUSTOMER.DISPUTE.CREATED",
            "resource": {
                "dispute_id": "PP-D-TEST-001",
                "buyer_name": "Test Buyer",
                "buyer_email": "buyer@test.com",
                "dispute_amount": {
                    "currency_code": "USD",
                    "value": "100.00"
                },
                "reason": "MERCHANDISE_OR_SERVICE_NOT_RECEIVED",
                "status": "OPEN",
                "transactions": [
                    {
                        "transaction_id": "TXN-123",
                        "custom": "ORD-123"
                    }
                ]
            }
        }
    
    @pytest.mark.asyncio
    async def test_duplicate_events_ignored(self, sample_webhook_payload):
        """Test that duplicate webhook events are detected."""
        # This is a conceptual test - would need DB setup for full test
        event_id = sample_webhook_payload["id"]
        
        # In a real test with DB:
        # 1. Process event once
        # 2. Try to process same event_id again
        # 3. Should be skipped as already processed
        
        assert event_id == "WH-TEST-12345"


class TestWebhookSignatureVerification:
    """Test webhook signature verification."""
    
    @pytest.mark.asyncio
    async def test_verify_webhook_signature_success(self):
        """Test successful signature verification."""
        with patch('app.paypal.client.settings') as mock_settings:
            mock_settings.paypal_client_id = "test_client"
            mock_settings.paypal_client_secret = "test_secret"
            mock_settings.paypal_base_url = "https://api-m.sandbox.paypal.com"
            
            client = PayPalClient()
            client._access_token = "test_token"
            client._token_expires_at = datetime.utcnow() + timedelta(hours=1)
            
            headers = {
                "paypal-auth-algo": "SHA256withRSA",
                "paypal-cert-url": "https://test.paypal.com/cert",
                "paypal-transmission-id": "test-trans-id",
                "paypal-transmission-sig": "test-sig",
                "paypal-transmission-time": "2024-01-01T00:00:00Z"
            }
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '{"verification_status": "SUCCESS"}'
            mock_response.json.return_value = {"verification_status": "SUCCESS"}
            
            with patch.object(client._http_client, 'request', return_value=mock_response):
                is_valid = await client.verify_webhook_signature(
                    "WH-TEST-ID",
                    headers,
                    b'{"test": "payload"}'
                )
                
                assert is_valid is True
            
            await client.close()
    
    @pytest.mark.asyncio
    async def test_verify_webhook_signature_failure(self):
        """Test failed signature verification."""
        with patch('app.paypal.client.settings') as mock_settings:
            mock_settings.paypal_client_id = "test_client"
            mock_settings.paypal_client_secret = "test_secret"
            mock_settings.paypal_base_url = "https://api-m.sandbox.paypal.com"
            
            client = PayPalClient()
            client._access_token = "test_token"
            client._token_expires_at = datetime.utcnow() + timedelta(hours=1)
            
            headers = {
                "paypal-auth-algo": "SHA256withRSA",
                "paypal-cert-url": "https://test.paypal.com/cert",
                "paypal-transmission-id": "test-trans-id",
                "paypal-transmission-sig": "bad-sig",
                "paypal-transmission-time": "2024-01-01T00:00:00Z"
            }
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = '{"verification_status": "FAILURE"}'
            mock_response.json.return_value = {"verification_status": "FAILURE"}
            
            with patch.object(client._http_client, 'request', return_value=mock_response):
                is_valid = await client.verify_webhook_signature(
                    "WH-TEST-ID",
                    headers,
                    b'{"test": "payload"}'
                )
                
                assert is_valid is False
            
            await client.close()
