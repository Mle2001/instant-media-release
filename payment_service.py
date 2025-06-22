"""
Payment Service - VNPay, PayPal, Stripe Integration
Payment processing, order management, và webhook handling
"""

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel
import httpx
import logging
from agno.tools import Toolkit
from agno.agent import Agent
from agno.models.openai import OpenAI
import sqlite3

logger = logging.getLogger(__name__)

class PaymentStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class PaymentProvider(Enum):
    VNPAY = "vnpay"
    PAYPAL = "paypal"
    STRIPE = "stripe"
    BANK_TRANSFER = "bank_transfer"

class PaymentRequest(BaseModel):
    order_id: str
    amount: float
    currency: str = "VND"
    provider: PaymentProvider
    description: str
    customer_info: Dict[str, Any]
    return_url: str
    cancel_url: str

class PaymentResponse(BaseModel):
    payment_id: str
    order_id: str
    status: PaymentStatus
    payment_url: Optional[str] = None
    qr_code: Optional[str] = None
    message: str
    expires_at: Optional[datetime] = None

class Order(BaseModel):
    order_id: str
    session_id: str
    package_type: str  # STARTER, STANDARD, PREMIUM
    amount: float
    currency: str = "VND"
    status: PaymentStatus
    customer_info: Dict[str, Any]
    media_plan: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None

class PaymentToolkit(Toolkit):
    """Custom toolkit cho payment processing"""
    
    def __init__(self, vnpay_config: Dict = None, paypal_config: Dict = None):
        self.vnpay_config = vnpay_config or {}
        self.paypal_config = paypal_config or {}
        
        super().__init__(
            name="payment_toolkit",
            tools=[
                self.create_payment,
                self.verify_payment,
                self.get_payment_status,
                self.create_vnpay_url,
                self.verify_vnpay_return
            ]
        )
    
    def create_payment(self, payment_request: PaymentRequest) -> PaymentResponse:
        """Tạo payment request cho provider tương ứng"""
        try:
            if payment_request.provider == PaymentProvider.VNPAY:
                return self._create_vnpay_payment(payment_request)
            elif payment_request.provider == PaymentProvider.PAYPAL:
                return self._create_paypal_payment(payment_request)
            elif payment_request.provider == PaymentProvider.BANK_TRANSFER:
                return self._create_bank_transfer(payment_request)
            else:
                raise ValueError(f"Unsupported payment provider: {payment_request.provider}")
                
        except Exception as e:
            logger.error(f"Payment creation failed: {e}")
            return PaymentResponse(
                payment_id="",
                order_id=payment_request.order_id,
                status=PaymentStatus.FAILED,
                message=f"Tạo thanh toán thất bại: {str(e)}"
            )
    
    def _create_vnpay_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Tạo VNPay payment URL"""
        payment_id = str(uuid.uuid4())
        
        # VNPay parameters
        vnp_params = {
            'vnp_Version': '2.1.0',
            'vnp_Command': 'pay',
            'vnp_TmnCode': self.vnpay_config.get('tmn_code', ''),
            'vnp_Amount': str(int(request.amount * 100)),  # VNPay expects amount in cents
            'vnp_CurrCode': 'VND',
            'vnp_TxnRef': payment_id,
            'vnp_OrderInfo': request.description,
            'vnp_OrderType': 'other',
            'vnp_Locale': 'vn',
            'vnp_ReturnUrl': request.return_url,
            'vnp_IpAddr': '127.0.0.1',
            'vnp_CreateDate': datetime.now().strftime('%Y%m%d%H%M%S')
        }
        
        # Create secure hash
        query_string = '&'.join([f"{k}={v}" for k, v in sorted(vnp_params.items())])
        vnp_hash = hmac.new(
            self.vnpay_config.get('hash_secret', '').encode(),
            query_string.encode(),
            hashlib.sha512
        ).hexdigest()
        
        payment_url = f"{self.vnpay_config.get('payment_url')}?{query_string}&vnp_SecureHash={vnp_hash}"
        
        # Save payment record
        self._save_payment_record(payment_id, request.order_id, PaymentStatus.PENDING)
        
        return PaymentResponse(
            payment_id=payment_id,
            order_id=request.order_id,
            status=PaymentStatus.PENDING,
            payment_url=payment_url,
            message="VNPay payment URL được tạo thành công",
            expires_at=datetime.now() + timedelta(minutes=15)
        )
    
    def _create_paypal_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Tạo PayPal payment (simplified)"""
        payment_id = str(uuid.uuid4())
        
        # PayPal API integration would go here
        # For demo purposes, return mock response
        
        return PaymentResponse(
            payment_id=payment_id,
            order_id=request.order_id,
            status=PaymentStatus.PENDING,
            payment_url=f"https://www.paypal.com/checkoutnow?token={payment_id}",
            message="PayPal payment được tạo thành công",
            expires_at=datetime.now() + timedelta(hours=1)
        )
    
    def _create_bank_transfer(self, request: PaymentRequest) -> PaymentResponse:
        """Tạo bank transfer instructions"""
        payment_id = str(uuid.uuid4())
        
        bank_info = {
            "bank_name": "Vietcombank",
            "account_number": "0123456789",
            "account_name": "CONG TY INSTANT MEDIA RELEASE",
            "transfer_content": f"IMR {request.order_id}",
            "amount": request.amount
        }
        
        return PaymentResponse(
            payment_id=payment_id,
            order_id=request.order_id,
            status=PaymentStatus.PENDING,
            qr_code=self._generate_bank_qr(bank_info),
            message="Thông tin chuyển khoản được tạo thành công",
            expires_at=datetime.now() + timedelta(days=1)
        )
    
    def verify_payment(self, payment_id: str, provider_data: Dict) -> PaymentStatus:
        """Xác minh payment status từ provider"""
        try:
            if 'vnp_' in provider_data:
                return self._verify_vnpay_payment(payment_id, provider_data)
            elif 'paypal_' in provider_data:
                return self._verify_paypal_payment(payment_id, provider_data)
            else:
                return PaymentStatus.FAILED
        except Exception as e:
            logger.error(f"Payment verification failed: {e}")
            return PaymentStatus.FAILED
    
    def get_payment_status(self, payment_id: str) -> PaymentStatus:
        """Lấy payment status từ database"""
        try:
            conn = sqlite3.connect('media_release.db')
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT status FROM payments WHERE payment_id = ?",
                (payment_id,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return PaymentStatus(result[0])
            return PaymentStatus.FAILED
            
        except Exception as e:
            logger.error(f"Get payment status failed: {e}")
            return PaymentStatus.FAILED
    
    def create_vnpay_url(self, order_id: str, amount: float, description: str) -> str:
        """Helper function để tạo VNPay URL nhanh"""
        request = PaymentRequest(
            order_id=order_id,
            amount=amount,
            provider=PaymentProvider.VNPAY,
            description=description,
            customer_info={},
            return_url="http://localhost:8000/api/payment/vnpay/return",
            cancel_url="http://localhost:8000/api/payment/cancel"
        )
        response = self._create_vnpay_payment(request)
        return response.payment_url or ""
    
    def verify_vnpay_return(self, vnp_params: Dict) -> bool:
        """Xác minh VNPay return từ webhook"""
        try:
            vnp_secure_hash = vnp_params.pop('vnp_SecureHash', '')
            
            # Sort parameters
            sorted_params = dict(sorted(vnp_params.items()))
            query_string = '&'.join([f"{k}={v}" for k, v in sorted_params.items()])
            
            # Verify hash
            expected_hash = hmac.new(
                self.vnpay_config.get('hash_secret', '').encode(),
                query_string.encode(),
                hashlib.sha512
            ).hexdigest()
            
            return hmac.compare_digest(vnp_secure_hash, expected_hash)
            
        except Exception as e:
            logger.error(f"VNPay verification failed: {e}")
            return False
    
    def _save_payment_record(self, payment_id: str, order_id: str, status: PaymentStatus):
        """Lưu payment record vào database"""
        try:
            conn = sqlite3.connect('media_release.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO payments 
                (payment_id, order_id, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                payment_id, order_id, status.value, 
                datetime.now().isoformat(), datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Save payment record failed: {e}")
    
    def _generate_bank_qr(self, bank_info: Dict) -> str:
        """Generate QR code cho bank transfer"""
        # Simplified QR generation
        qr_data = f"BANK:{bank_info['account_number']}:{bank_info['amount']}:{bank_info['transfer_content']}"
        return f"data:image/png;base64,{qr_data}"  # Mock QR code

class OrderManager:
    """Quản lý orders và lifecycle"""
    
    def __init__(self):
        self.payment_toolkit = PaymentToolkit()
        self._init_database()
    
    def _init_database(self):
        """Khởi tạo database tables cho orders và payments"""
        conn = sqlite3.connect('media_release.db')
        cursor = conn.cursor()
        
        # Orders table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                package_type TEXT NOT NULL,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'VND',
                status TEXT NOT NULL,
                customer_info TEXT,
                media_plan TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                expires_at TEXT
            )
        """)
        
        # Payments table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id TEXT PRIMARY KEY,
                order_id TEXT NOT NULL,
                provider TEXT,
                status TEXT NOT NULL,
                amount REAL,
                provider_transaction_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders (order_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_order(self, session_id: str, package_type: str, 
                    amount: float, customer_info: Dict, media_plan: Dict) -> Order:
        """Tạo order mới"""
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        
        order = Order(
            order_id=order_id,
            session_id=session_id,
            package_type=package_type,
            amount=amount,
            status=PaymentStatus.PENDING,
            customer_info=customer_info,
            media_plan=media_plan,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=24)
        )
        
        # Save to database
        self._save_order(order)
        return order
    
    def get_order(self, order_id: str) -> Optional[Order]:
        """Lấy order theo ID"""
        try:
            conn = sqlite3.connect('media_release.db')
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM orders WHERE order_id = ?",
                (order_id,)
            )
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return Order(
                    order_id=result[0],
                    session_id=result[1],
                    package_type=result[2],
                    amount=result[3],
                    currency=result[4],
                    status=PaymentStatus(result[5]),
                    customer_info=json.loads(result[6]),
                    media_plan=json.loads(result[7]),
                    created_at=datetime.fromisoformat(result[8]),
                    updated_at=datetime.fromisoformat(result[9]),
                    expires_at=datetime.fromisoformat(result[10]) if result[10] else None
                )
            return None
            
        except Exception as e:
            logger.error(f"Get order failed: {e}")
            return None
    
    def update_order_status(self, order_id: str, status: PaymentStatus) -> bool:
        """Cập nhật order status"""
        try:
            conn = sqlite3.connect('media_release.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE orders 
                SET status = ?, updated_at = ?
                WHERE order_id = ?
            """, (status.value, datetime.now().isoformat(), order_id))
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
            
        except Exception as e:
            logger.error(f"Update order status failed: {e}")
            return False
    
    def _save_order(self, order: Order):
        """Lưu order vào database"""
        try:
            conn = sqlite3.connect('media_release.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO orders 
                (order_id, session_id, package_type, amount, currency, status, 
                 customer_info, media_plan, created_at, updated_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                order.order_id, order.session_id, order.package_type,
                order.amount, order.currency, order.status.value,
                json.dumps(order.customer_info), json.dumps(order.media_plan),
                order.created_at.isoformat(), order.updated_at.isoformat(),
                order.expires_at.isoformat() if order.expires_at else None
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Save order failed: {e}")

# Payment Agent cho Agno framework
class PaymentAgent(Agent):
    """AI Agent chuyên xử lý payments và orders"""
    
    def __init__(self):
        self.order_manager = OrderManager()
        self.payment_toolkit = PaymentToolkit()
        
        super().__init__(
            model=OpenAI(id="gpt-4"),
            tools=[self.payment_toolkit],
            instructions=[
                "Bạn là Payment Agent chuyên xử lý thanh toán và quản lý đơn hàng",
                "Hỗ trợ VNPay, PayPal, Stripe và chuyển khoản ngân hàng",
                "Luôn xác minh thông tin thanh toán và đảm bảo bảo mật",
                "Cung cấp hướng dẫn thanh toán rõ ràng bằng tiếng Việt",
                "Xử lý webhook và cập nhật trạng thái đơn hàng tự động"
            ],
            description="AI Agent xử lý thanh toán và quản lý đơn hàng cho hệ thống Instant Media Release"
        )
    
    def process_payment_request(self, session_id: str, package_type: str, 
                              amount: float, customer_info: Dict, 
                              media_plan: Dict, provider: PaymentProvider) -> PaymentResponse:
        """Xử lý yêu cầu thanh toán hoàn chỉnh"""
        
        # 1. Tạo order
        order = self.order_manager.create_order(
            session_id=session_id,
            package_type=package_type,
            amount=amount,
            customer_info=customer_info,
            media_plan=media_plan
        )
        
        # 2. Tạo payment request
        payment_request = PaymentRequest(
            order_id=order.order_id,
            amount=amount,
            provider=provider,
            description=f"Gói {package_type} - Instant Media Release",
            customer_info=customer_info,
            return_url="http://localhost:8000/api/payment/success",
            cancel_url="http://localhost:8000/api/payment/cancel"
        )
        
        # 3. Xử lý payment với provider
        response = self.payment_toolkit.create_payment(payment_request)
        
        return response
    
    def handle_payment_webhook(self, provider: str, webhook_data: Dict) -> bool:
        """Xử lý webhook từ payment providers"""
        try:
            if provider == "vnpay":
                return self._handle_vnpay_webhook(webhook_data)
            elif provider == "paypal":
                return self._handle_paypal_webhook(webhook_data)
            else:
                logger.warning(f"Unknown payment provider webhook: {provider}")
                return False
                
        except Exception as e:
            logger.error(f"Webhook handling failed: {e}")
            return False
    
    def _handle_vnpay_webhook(self, data: Dict) -> bool:
        """Xử lý VNPay webhook"""
        if not self.payment_toolkit.verify_vnpay_return(data):
            return False
        
        payment_id = data.get('vnp_TxnRef')
        response_code = data.get('vnp_ResponseCode')
        
        if response_code == '00':  # Success
            status = PaymentStatus.COMPLETED
        else:
            status = PaymentStatus.FAILED
        
        # Update payment và order status
        return self._update_payment_status(payment_id, status)
    
    def _update_payment_status(self, payment_id: str, status: PaymentStatus) -> bool:
        """Cập nhật payment và order status"""
        try:
            # Update payment
            conn = sqlite3.connect('media_release.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE payments 
                SET status = ?, updated_at = ?
                WHERE payment_id = ?
            """, (status.value, datetime.now().isoformat(), payment_id))
            
            # Get order_id
            cursor.execute(
                "SELECT order_id FROM payments WHERE payment_id = ?",
                (payment_id,)
            )
            result = cursor.fetchone()
            
            if result:
                order_id = result[0]
                # Update order status
                cursor.execute("""
                    UPDATE orders 
                    SET status = ?, updated_at = ?
                    WHERE order_id = ?
                """, (status.value, datetime.now().isoformat(), order_id))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Update payment status failed: {e}")
            return False

# Package pricing configuration
PACKAGE_PRICING = {
    "STARTER": {
        "price": 12_000_000,  # 12M VND
        "features": ["2-3 báo chí tier-2", "1-3 ngày", "Chỉnh sửa nhẹ", "Báo cáo cơ bản"],
        "media_count": 3,
        "timeline": "1-3 ngày"
    },
    "STANDARD": {
        "price": 30_000_000,  # 30M VND
        "features": ["12-15 báo chí với tier-1", "5-7 ngày", "Viết đầy đủ", "Báo cáo chi tiết"],
        "media_count": 15,
        "timeline": "5-7 ngày"
    },
    "PREMIUM": {
        "price": 50_000_000,  # 50M VND
        "features": ["15-18 báo chí + phỏng vấn", "10-14 ngày", "Chiến lược + viết", "Social media", "Tư vấn PR"],
        "media_count": 18,
        "timeline": "10-14 ngày"
    }
}

def get_package_info(package_type: str) -> Dict:
    """Lấy thông tin package pricing"""
    return PACKAGE_PRICING.get(package_type.upper(), {})

if __name__ == "__main__":
    # Test payment system
    payment_agent = PaymentAgent()
    
    # Test create order
    test_order = payment_agent.order_manager.create_order(
        session_id="test-session",
        package_type="STANDARD",
        amount=30_000_000,
        customer_info={"name": "Test User", "email": "test@example.com"},
        media_plan={"media_count": 15, "target_audience": "SME"}
    )
    
    print(f"✅ Test order created: {test_order.order_id}")
    
    # Test payment request
    response = payment_agent.process_payment_request(
        session_id="test-session",
        package_type="STANDARD",
        amount=30_000_000,
        customer_info={"name": "Test User", "email": "test@example.com"},
        media_plan={"media_count": 15},
        provider=PaymentProvider.VNPAY
    )
    
    print(f"✅ Payment response: {response.message}")