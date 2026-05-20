import logging
import json
import time

logger = logging.getLogger(__name__)

class CJDropshippingClient:
    """
    CJ Dropshipping API automation integration.
    Supports a fully-functional sandbox mock mode out of the box to test dropshipping order fulfillment.
    """
    def __init__(self, api_key=None, access_token=None, use_sandbox=True):
        self.api_key = api_key
        self.access_token = access_token
        self.use_sandbox = use_sandbox
        self.api_url = "https://developers.cjdropshipping.com/api2.0/v1" if not use_sandbox else "https://sandbox-api.cjdropshipping.com"

    def get_headers(self):
        return {
            "Content-Type": "application/json",
            "CJ-Access-Token": self.access_token or "mock_access_token_12345"
        }

    def sync_product(self, cj_product_id):
        """
        Synchronizes product details and stock information from CJ Dropshipping.
        If in sandbox/mock mode, simulates a successful product retrieval and updates local SKU database.
        """
        logger.info(f"Syncing CJ Product ID: {cj_product_id}")
        
        if self.use_sandbox:
            # Simulate a successful CJ Dropshipping API product retrieval
            time.sleep(0.5) # simulate latency
            return {
                "success": True,
                "product_id": cj_product_id,
                "title": "AeroGlide Max Pro - Ergonomic Wireless Gaming Mouse",
                "sku": "AG-MAX-PRO-01",
                "price": 1899.00,
                "compare_at_price": 2999.00,
                "inventory": 142,
                "images": [
                    "https://images.unsplash.com/photo-1615663245857-ac93bb7c39e7?w=800&auto=format&fit=crop",
                    "https://images.unsplash.com/photo-1625842268584-8f3290447036?w=800&auto=format&fit=crop",
                    "https://images.unsplash.com/photo-1527814050087-3b952115a601?w=800&auto=format&fit=crop"
                ],
                "description": "Mocked CJ Dropshipping synced descriptions."
            }
        
        # Real HTTP request logic (implemented here for production prep)
        try:
            import requests
            url = f"{self.api_url}/product/detail?pid={cj_product_id}"
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    return {
                        "success": True,
                        "data": data.get("data")
                    }
            return {"success": False, "error": f"API Error: {response.status_code}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def forward_order(self, order):
        """
        Automatically posts checkout order details to CJ Dropshipping order center.
        For MVP, saves merchant manually copy-pasting customer details.
        """
        logger.info(f"Forwarding order #{order.id} for {order.product.title} to CJ Dropshipping")
        
        payload = {
            "orderNumber": f"KELS-ORDER-{order.id}",
            "shippingAddress": {
                "fullName": order.full_name,
                "phoneNumber": order.phone_number,
                "addressLine": order.shipping_address,
                "countryCode": "PH",
            },
            "items": [
                {
                    "sku": order.product.sku or "AG-MAX-PRO-01",
                    "quantity": 1,
                    "cjProductId": order.product.cj_product_id
                }
            ]
        }

        if self.use_sandbox:
            # Simulate a successful CJ Dropshipping API order submission
            time.sleep(0.5) # simulate network latency
            logger.info(f"Successfully mock-fulfilled order #{order.id} to CJ Dropshipping Sandbox!")
            return {
                "success": True,
                "cj_order_id": f"CJ-ORD-{int(time.time())}",
                "status": "Submitted to CJ Dropshipping Center",
                "payload": payload
            }

        # Real HTTP POST order submission prep
        try:
            import requests
            url = f"{self.api_url}/shoppingCart/add"
            response = requests.post(url, headers=self.get_headers(), data=json.dumps(payload), timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    return {
                        "success": True,
                        "cj_order_id": data.get("data", {}).get("orderId"),
                        "status": "Submitted to CJ"
                    }
            return {"success": False, "error": f"Failed to forward: {response.text}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_inventory(self, sku):
        """Checks the stock inventory levels of a product SKU directly on CJ warehouses."""
        if self.use_sandbox:
            import random
            return {
                "success": True,
                "sku": sku,
                "stock": random.randint(50, 200)
            }
            
        try:
            import requests
            url = f"{self.api_url}/product/stock?sku={sku}"
            response = requests.get(url, headers=self.get_headers(), timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 200:
                    return {
                        "success": True,
                        "stock": data.get("data", {}).get("stock", 0)
                    }
            return {"success": False, "stock": 0}
        except Exception:
            return {"success": False, "stock": 0}
