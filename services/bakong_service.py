import base64
import hashlib
from io import BytesIO
import requests
import qrcode
from config import Config
from bakong_khqr import KHQR

class BakongService:
    def __init__(self):
        self.bakong_id = Config.BAKONG_ID
        self.merchant_name = Config.BAKONG_MERCHANT_NAME
        self.merchant_city = Config.BAKONG_MERCHANT_CITY
        self.api_base_url = Config.BAKONG_API_BASE_URL.rstrip('/')
        self.token = Config.BAKONG_TOKEN
        self.khqr_client = KHQR(self.token)

    def generate_khqr(self, order_number: str, amount: float, currency: str = "USD"):
        """
        Generates dynamic KHQR string, MD5 hash, and QR code base64 image.
        """
        amount_rounded = round(float(amount), 2)

        try:
            khqr_resp = self.khqr_client.create_qr(
                account_id=self.bakong_id,
                merchant_name=self.merchant_name,
                merchant_city=self.merchant_city,
                amount=amount_rounded,
                currency=currency,
                bill_number=str(order_number)[:25]
            )
            if hasattr(khqr_resp, 'qr'):
                qr_string = khqr_resp.qr
            elif isinstance(khqr_resp, dict) and 'qr' in khqr_resp:
                qr_string = khqr_resp['qr']
            else:
                qr_string = str(khqr_resp)
        except Exception as e:
            # Fallback direct generation if needed
            raise RuntimeError(f"Failed to generate Bakong KHQR: {e}")

        # Compute MD5
        try:
            md5 = self.khqr_client.generate_md5(qr_string)
        except Exception:
            md5 = hashlib.md5(qr_string.encode('utf-8')).hexdigest()

        # Generate QR code image as base64 PNG
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(qr_string)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#111827", back_color="#ffffff")

        buffered = BytesIO()
        img.save(buffered, format="PNG")
        qr_base64 = "data:image/png;base64," + base64.b64encode(buffered.getvalue()).decode("utf-8")

        return {
            "qr_string": qr_string,
            "md5": md5,
            "qr_image": qr_base64,
            "amount": amount_rounded,
            "currency": currency,
            "merchant_name": self.merchant_name
        }

    def check_transaction(self, md5: str):
        """
        Calls NBC Bakong endpoint to check transaction status by md5.
        Endpoint: POST /v1/check_transaction_by_md5
        Returns dict: {"paid": bool, "data": dict or None, "message": str}
        """
        if not md5:
            return {"paid": False, "data": None, "message": "MD5 hash is required"}

        url = f"{self.api_base_url}/v1/check_transaction_by_md5"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {"md5": md5}

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                result = response.json()
                # Bakong responseCode == 0 means paid and confirmed!
                if result.get("responseCode") == 0:
                    data = result.get("data") or {}
                    return {
                        "paid": True,
                        "data": data,
                        "transaction_hash": data.get("hash") or data.get("externalRef") or "",
                        "external_ref": data.get("externalRef") or "",
                        "message": "Payment successful!"
                    }
                else:
                    return {
                        "paid": False,
                        "data": None,
                        "message": result.get("responseMessage") or "Transaction not found or pending"
                    }
            else:
                return {
                    "paid": False,
                    "data": None,
                    "message": f"Bakong API returned status {response.status_code}"
                }
        except Exception as e:
            return {
                "paid": False,
                "data": None,
                "message": f"Error contacting Bakong API: {str(e)}"
            }

bakong_service = BakongService()
