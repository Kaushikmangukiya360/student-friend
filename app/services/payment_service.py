from typing import Dict, Any, Optional, List
import uuid
from datetime import datetime, timedelta
from app.db.connection import get_database
from bson import ObjectId
import hashlib
import hmac
import os


class PaymentService:
    """Enhanced payment service supporting multiple gateways and methods"""
    
    def __init__(self):
        self.supported_gateways = ["razorpay", "stripe", "paypal"]
        self.supported_currencies = ["INR", "USD", "EUR"]
        self.supported_payment_methods = ["card", "upi", "wallet", "netbanking", "bank_transfer"]
        self.default_gateway = "razorpay"
        
        # Gateway configurations (would be loaded from environment)
        self.gateway_configs = {
            "razorpay": {
                "key_id": os.getenv("RAZORPAY_KEY_ID", "rzp_test_mock"),
                "key_secret": os.getenv("RAZORPAY_KEY_SECRET", "mock_secret"),
                "webhook_secret": os.getenv("RAZORPAY_WEBHOOK_SECRET", "mock_webhook")
            },
            "stripe": {
                "publishable_key": os.getenv("STRIPE_PUBLISHABLE_KEY", "pk_test_mock"),
                "secret_key": os.getenv("STRIPE_SECRET_KEY", "sk_test_mock"),
                "webhook_secret": os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_mock")
            },
            "paypal": {
                "client_id": os.getenv("PAYPAL_CLIENT_ID", "mock_client_id"),
                "client_secret": os.getenv("PAYPAL_CLIENT_SECRET", "mock_client_secret"),
                "webhook_id": os.getenv("PAYPAL_WEBHOOK_ID", "mock_webhook_id")
            }
        }
    
    async def initiate_payment(
        self,
        user_id: str,
        amount: float,
        currency: str = "INR",
        purpose: str = "wallet_recharge",
        gateway: str = "razorpay",
        metadata: Dict[str, Any] = None,
        payment_method: str = "card"
    ) -> Dict[str, Any]:
        """Initiate a payment transaction with multiple gateway support"""
        
        if gateway not in self.supported_gateways:
            raise ValueError(f"Unsupported gateway: {gateway}")
        
        if currency not in self.supported_currencies:
            raise ValueError(f"Unsupported currency: {currency}")
        
        if payment_method not in self.supported_payment_methods:
            raise ValueError(f"Unsupported payment method: {payment_method}")
        
        # Generate payment IDs
        payment_id = f"pay_{uuid.uuid4().hex[:16]}"
        order_id = f"order_{uuid.uuid4().hex[:16]}"
        
        # Calculate fees based on gateway and method
        fee_amount = self._calculate_fees(amount, gateway, payment_method)
        total_amount = amount + fee_amount
        
        # Create payment data
        payment_data = {
            "payment_id": payment_id,
            "order_id": order_id,
            "user_id": user_id,
            "amount": amount,
            "fee_amount": fee_amount,
            "total_amount": total_amount,
            "currency": currency,
            "purpose": purpose,
            "gateway": gateway,
            "payment_method": payment_method,
            "status": "created",
            "metadata": metadata or {},
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=30)
        }
        
        # Store payment in database
        db = get_database()
        await db.payments.insert_one(payment_data)
        
        # Generate gateway-specific response
        gateway_response = await self._generate_gateway_response(
            payment_data, gateway
        )
        
        return {
            "payment_id": payment_id,
            "order_id": order_id,
            "amount": amount,
            "fee_amount": fee_amount,
            "total_amount": total_amount,
            "currency": currency,
            "gateway": gateway,
            "payment_method": payment_method,
            "status": "created",
            "gateway_data": gateway_response,
            "expires_at": payment_data["expires_at"]
        }
    
    def _calculate_fees(self, amount: float, gateway: str, payment_method: str) -> float:
        """Calculate transaction fees based on gateway and payment method"""
        fee_rates = {
            "razorpay": {
                "card": 0.0299,  # 2.99%
                "upi": 0.0,      # Free
                "wallet": 0.0199, # 1.99%
                "netbanking": 0.0199, # 1.99%
                "bank_transfer": 0.0   # Free
            },
            "stripe": {
                "card": 0.029,  # 2.9% + 30¢
                "upi": 0.029,
                "wallet": 0.029,
                "netbanking": 0.029,
                "bank_transfer": 0.029
            },
            "paypal": {
                "card": 0.029,  # 2.9% + 30¢
                "upi": 0.029,
                "wallet": 0.029,
                "netbanking": 0.029,
                "bank_transfer": 0.029
            }
        }
        
        base_rate = fee_rates.get(gateway, {}).get(payment_method, 0.02)
        fee = amount * base_rate
        
        # Add fixed fees for some gateways
        if gateway == "stripe":
            fee += 0.30
        elif gateway == "paypal":
            fee += 0.30
        
        return round(fee, 2)
    
    async def _generate_gateway_response(self, payment_data: Dict[str, Any], gateway: str) -> Dict[str, Any]:
        """Generate gateway-specific response data"""
        
        if gateway == "razorpay":
            return {
                "key_id": self.gateway_configs["razorpay"]["key_id"],
                "order_id": payment_data["order_id"],
                "amount": int(payment_data["total_amount"] * 100),  # Paise
                "currency": payment_data["currency"],
                "name": "StudyFriend",
                "description": f"Payment for {payment_data['purpose']}",
                "prefill": {
                    "email": "user@example.com",  # Would be fetched from user data
                    "contact": "9999999999"
                }
            }
        
        elif gateway == "stripe":
            return {
                "client_secret": f"cs_test_{uuid.uuid4().hex[:24]}",
                "amount": int(payment_data["total_amount"] * 100),  # Cents
                "currency": payment_data["currency"].lower(),
                "metadata": {
                    "order_id": payment_data["order_id"],
                    "purpose": payment_data["purpose"]
                }
            }
        
        elif gateway == "paypal":
            return {
                "order_id": f"PAYPAL_{payment_data['order_id']}",
                "amount": {
                    "value": str(payment_data["total_amount"]),
                    "currency_code": payment_data["currency"]
                },
                "intent": "CAPTURE"
            }
        
        return {}
    
    async def verify_payment(
        self,
        payment_id: str,
        order_id: str,
        signature: str = None,
        gateway_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Verify a payment transaction with enhanced validation"""
        
        db = get_database()
        
        # Find payment
        payment = await db.payments.find_one({"payment_id": payment_id})
        
        if not payment:
            return {
                "success": False,
                "message": "Payment not found"
            }
        
        # Check if payment is expired
        if payment["expires_at"] < datetime.utcnow():
            await db.payments.update_one(
                {"payment_id": payment_id},
                {"$set": {"status": "expired"}}
            )
            return {
                "success": False,
                "message": "Payment has expired"
            }
        
        # Verify signature based on gateway
        if not await self._verify_gateway_signature(payment, signature, gateway_data):
            return {
                "success": False,
                "message": "Invalid payment signature"
            }
        
        # Update payment status
        update_data = {
            "status": "completed",
            "verified_at": datetime.utcnow(),
            "signature": signature,
            "gateway_response": gateway_data
        }
        
        await db.payments.update_one(
            {"payment_id": payment_id},
            {"$set": update_data}
        )
        
        # Update user wallet if applicable
        if payment.get("purpose") == "wallet_recharge":
            await db.users.update_one(
                {"_id": ObjectId(payment["user_id"])},
                {"$inc": {"wallet_balance": payment["amount"]}}
            )
        
        # Create transaction record
        transaction = {
            "user_id": payment["user_id"],
            "amount": payment["amount"],
            "fee_amount": payment["fee_amount"],
            "type": "credit",
            "purpose": payment.get("purpose", "payment"),
            "reference_id": payment_id,
            "gateway": payment["gateway"],
            "payment_method": payment["payment_method"],
            "timestamp": datetime.utcnow()
        }
        await db.transactions.insert_one(transaction)
        
        return {
            "success": True,
            "message": "Payment verified successfully",
            "payment_id": payment_id,
            "status": "completed",
            "amount": payment["amount"],
            "fee_amount": payment["fee_amount"]
        }
    
    async def _verify_gateway_signature(
        self, 
        payment: Dict[str, Any], 
        signature: str, 
        gateway_data: Dict[str, Any]
    ) -> bool:
        """Verify payment signature based on gateway"""
        
        gateway = payment["gateway"]
        
        if gateway == "razorpay":
            # Razorpay signature verification
            key_secret = self.gateway_configs["razorpay"]["key_secret"]
            order_id = payment["order_id"]
            payment_id = payment["payment_id"]
            
            message = f"{order_id}|{payment_id}"
            expected_signature = hmac.new(
                key_secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return signature == expected_signature
        
        elif gateway == "stripe":
            # Stripe webhook signature verification (simplified)
            return signature and signature.startswith("whsec_")
        
        elif gateway == "paypal":
            # PayPal verification (simplified)
            return gateway_data and gateway_data.get("status") == "COMPLETED"
        
        # For mock/testing purposes, accept any signature
        return True
    
    async def process_refund(
        self,
        payment_id: str,
        amount: float = None,
        reason: str = "customer_request"
    ) -> Dict[str, Any]:
        """Process a refund for a payment with enhanced tracking"""
        
        db = get_database()
        
        # Find payment
        payment = await db.payments.find_one({"payment_id": payment_id})
        
        if not payment:
            return {
                "success": False,
                "message": "Payment not found"
            }
        
        if payment["status"] != "completed":
            return {
                "success": False,
                "message": "Only completed payments can be refunded"
            }
        
        refund_amount = amount or payment["amount"]
        if refund_amount > payment["amount"]:
            return {
                "success": False,
                "message": "Refund amount cannot exceed payment amount"
            }
        
        refund_id = f"rfnd_{uuid.uuid4().hex[:16]}"
        
        # Mock refund API call (in production, call actual gateway API)
        await db.payments.update_one(
            {"payment_id": payment_id},
            {
                "$set": {
                    "status": "refunded",
                    "refund_id": refund_id,
                    "refund_amount": refund_amount,
                    "refund_reason": reason,
                    "refunded_at": datetime.utcnow()
                }
            }
        )
        
        # Update user wallet
        await db.users.update_one(
            {"_id": ObjectId(payment["user_id"])},
            {"$inc": {"wallet_balance": refund_amount}}
        )
        
        # Create transaction record
        transaction = {
            "user_id": payment["user_id"],
            "amount": refund_amount,
            "type": "credit",
            "purpose": "refund",
            "reference_id": refund_id,
            "gateway": payment["gateway"],
            "timestamp": datetime.utcnow(),
            "metadata": {"original_payment_id": payment_id, "reason": reason}
        }
        await db.transactions.insert_one(transaction)
        
        return {
            "success": True,
            "message": "Refund processed successfully",
            "refund_id": refund_id,
            "amount": refund_amount,
            "gateway": payment["gateway"]
        }
    
    async def get_payment_history(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        status: str = None
    ) -> List[Dict[str, Any]]:
        """Get payment history for a user"""
        
        db = get_database()
        
        query = {"user_id": user_id}
        if status:
            query["status"] = status
        
        payments = await db.payments.find(query)\
            .sort("created_at", -1)\
            .skip(offset)\
            .limit(limit)\
            .to_list(length=None)
        
        return payments
    
    async def get_transaction_history(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        transaction_type: str = None
    ) -> List[Dict[str, Any]]:
        """Get transaction history for a user"""
        
        db = get_database()
        
        query = {"user_id": user_id}
        if transaction_type:
            query["type"] = transaction_type
        
        transactions = await db.transactions.find(query)\
            .sort("timestamp", -1)\
            .skip(offset)\
            .limit(limit)\
            .to_list(length=None)
        
        return transactions
    
    async def handle_webhook(
        self,
        gateway: str,
        payload: Dict[str, Any],
        signature: str = None
    ) -> Dict[str, Any]:
        """Handle webhook notifications from payment gateways"""
        
        if not await self._verify_webhook_signature(gateway, payload, signature):
            return {
                "success": False,
                "message": "Invalid webhook signature"
            }
        
        # Process webhook based on gateway
        if gateway == "razorpay":
            return await self._process_razorpay_webhook(payload)
        elif gateway == "stripe":
            return await self._process_stripe_webhook(payload)
        elif gateway == "paypal":
            return await self._process_paypal_webhook(payload)
        
        return {
            "success": False,
            "message": f"Unsupported gateway: {gateway}"
        }
    
    async def _verify_webhook_signature(
        self, 
        gateway: str, 
        payload: Dict[str, Any], 
        signature: str
    ) -> bool:
        """Verify webhook signature"""
        # Implementation would verify webhook signatures
        # For now, return True for mock purposes
        return True
    
    async def _process_razorpay_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process Razorpay webhook"""
        event = payload.get("event")
        payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        
        if event == "payment.captured":
            payment_id = payment_entity.get("id")
            order_id = payment_entity.get("order_id")
            
            # Verify the payment
            return await self.verify_payment(
                payment_id=f"pay_{payment_id[-16:]}",  # Convert to our format
                order_id=order_id,
                gateway_data=payment_entity
            )
        
        return {"success": True, "message": f"Event {event} processed"}
    
    async def _process_stripe_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process Stripe webhook"""
        # Similar implementation for Stripe
        return {"success": True, "message": "Stripe webhook processed"}
    
    async def _process_paypal_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process PayPal webhook"""
        # Similar implementation for PayPal
        return {"success": True, "message": "PayPal webhook processed"}


# Singleton instance
payment_service = PaymentService()
