import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

class PayMongoClient:
    """
    PayMongo API client wrapper for Philippine E-Wallet and Card checkout sessions.
    Supports GCash, Maya, GrabPay, and Credit/Debit Cards.
    Includes a fully operational sandbox/mock fallback mode for seamless local development.
    """
    def __init__(self, secret_key=None):
        self.secret_key = secret_key or getattr(settings, 'PAYMONGO_SECRET_KEY', 'pm_mock_secret_key')
        self.api_url = "https://api.paymongo.com/v1"
        self.is_mock = self.secret_key.startswith("pm_mock")

    def get_headers(self):
        import base64
        # PayMongo uses basic auth with the secret key as the username and no password
        auth_str = f"{self.secret_key}:"
        auth_bytes = auth_str.encode("utf-8")
        auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")
        return {
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth_b64}"
        }

    def create_checkout_session(self, order, success_url, cancel_url):
        """
        Creates a PayMongo Checkout Session for the given Order.
        Calculates prices in centavos (PHP currency ₱ is in PHP, must multiply by 100).
        """
        logger.info(f"Creating PayMongo checkout session for Order #{order.id} (Price: {order.product.price})")
        
        # Calculate amount in centavos (e.g. 1899.00 -> 189900)
        amount_centavos = int(order.product.price * 100)
        
        # Structure payload
        payload = {
            "data": {
                "attributes": {
                    "billing": {
                        "name": order.full_name,
                        "phone": order.phone_number
                    },
                    "send_email_receipt": False,
                    "show_description": True,
                    "show_line_items": True,
                    "cancel_url": cancel_url,
                    "description": f"Payment for {order.product.title}",
                    "line_items": [
                        {
                            "amount": amount_centavos,
                            "currency": "PHP",
                            "name": order.product.title,
                            "quantity": 1
                        }
                    ],
                    "payment_method_types": [
                        "gcash",
                        "paymaya",
                        "grab_pay",
                        "card"
                    ],
                    "success_url": success_url
                }
            }
        }

        if self.is_mock:
            # Local development mock fallback
            mock_session_id = f"pm_mock_sess_{order.id}_12345"
            # In success_url, we replace {CHECKOUT_SESSION_ID} manually
            resolved_success_url = success_url.replace("{CHECKOUT_SESSION_ID}", mock_session_id)
            logger.info(f"[PAYMONGO MOCK] Simulating session creation. Redirecting to: {resolved_success_url}")
            return {
                "success": True,
                "session_id": mock_session_id,
                "checkout_url": resolved_success_url,
                "is_mock": True
            }

        try:
            url = f"{self.api_url}/checkout_sessions"
            response = requests.post(url, json=payload, headers=self.get_headers(), timeout=10)
            
            if response.status_code in [200, 201]:
                data = response.json().get("data", {})
                attributes = data.get("attributes", {})
                return {
                    "success": True,
                    "session_id": data.get("id"),
                    "checkout_url": attributes.get("checkout_url"),
                    "is_mock": False
                }
            else:
                err_msg = response.json().get("errors", [{}])[0].get("detail", "Unknown PayMongo API Error")
                logger.error(f"PayMongo API Error ({response.status_code}): {err_msg}")
                return {"success": False, "error": err_msg}
        except Exception as e:
            logger.exception("PayMongo request exception")
            return {"success": False, "error": str(e)}

    def retrieve_checkout_session(self, session_id):
        """
        Retrieves a Checkout Session from PayMongo using the session ID to check payment status.
        """
        logger.info(f"Retrieving PayMongo checkout session status: {session_id}")
        
        if self.is_mock or session_id.startswith("pm_mock"):
            logger.info(f"[PAYMONGO MOCK] Verifying mock checkout session: {session_id}")
            return {
                "success": True,
                "payment_status": "paid",
                "payment_intent_id": "pm_mock_intent_98765",
                "is_mock": True
            }

        try:
            url = f"{self.api_url}/checkout_sessions/{session_id}"
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            
            if response.status_code == 200:
                data = response.json().get("data", {})
                attributes = data.get("attributes", {})
                payments = attributes.get("payments", [])
                
                # Check status
                # Checkout sessions can have status: 'active', 'payment_success', 'payment_failed', 'expired'
                session_status = attributes.get("status")
                
                payment_status = "pending"
                payment_intent_id = None
                
                if session_status == "payment_success":
                    payment_status = "paid"
                    if payments:
                        payment_intent_id = payments[0].get("id")
                elif session_status == "payment_failed":
                    payment_status = "failed"
                elif session_status == "expired":
                    payment_status = "failed"

                return {
                    "success": True,
                    "payment_status": payment_status,
                    "payment_intent_id": payment_intent_id,
                    "is_mock": False
                }
            else:
                err_msg = response.json().get("errors", [{}])[0].get("detail", "Unknown PayMongo Retrieval Error")
                logger.error(f"PayMongo Retrieval API Error ({response.status_code}): {err_msg}")
                return {"success": False, "error": err_msg}
        except Exception as e:
            logger.exception("PayMongo retrieval request exception")
            return {"success": False, "error": str(e)}
