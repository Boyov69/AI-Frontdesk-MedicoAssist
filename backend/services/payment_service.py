"""
MedicoAssist.it — Payment Service (Stripe)
Manages subscriptions, checkout sessions, and usage tracking.
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class PaymentService:
    """Stripe payment service for MedicoAssist subscriptions."""

    def __init__(self):
        self.stripe = None
        self._initialized = False

    def initialize(self):
        """Initialize Stripe with API key."""
        if self._initialized:
            return True

        api_key = os.getenv("STRIPE_SECRET_KEY")
        if not api_key:
            logger.warning("[STRIPE] Secret key non configurata — pagamenti disabilitati")
            return False

        try:
            import stripe
            stripe.api_key = api_key
            self.stripe = stripe
            self._initialized = True
            logger.info("[STRIPE] ✅ Inizializzato")
            return True
        except ImportError:
            logger.warning("[STRIPE] ⚠️ Modulo stripe non installato")
            return False

    def create_checkout_session(
        self,
        price_id: str,
        customer_email: str,
        practice_id: str,
        success_url: str = "",
        cancel_url: str = "",
    ) -> Optional[str]:
        """Create a Stripe checkout session. Returns the checkout URL."""
        if not self._initialized:
            return None

        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        success = success_url or f"{frontend_url}/dashboard?payment=success"
        cancel = cancel_url or f"{frontend_url}/pricing?payment=cancelled"

        try:
            session = self.stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{"price": price_id, "quantity": 1}],
                mode="subscription",
                success_url=success,
                cancel_url=cancel,
                customer_email=customer_email,
                metadata={"practice_id": practice_id},
            )
            logger.info(f"[STRIPE] Checkout creato: {session.id}")
            return session.url
        except Exception as e:
            logger.error(f"[STRIPE] Errore checkout: {e}")
            return None

    def get_subscription_status(self, customer_id: str) -> Dict[str, Any]:
        """Get subscription status for a customer."""
        if not self._initialized:
            return {"active": False, "reason": "Servizio non inizializzato"}

        try:
            subs = self.stripe.Subscription.list(customer=customer_id, limit=1)
            if subs.data:
                sub = subs.data[0]
                return {
                    "active": sub.status == "active",
                    "plan": sub.plan.id if sub.plan else None,
                    "status": sub.status,
                    "current_period_end": sub.current_period_end,
                }
            return {"active": False, "reason": "Nessun abbonamento trovato"}
        except Exception as e:
            logger.error(f"[STRIPE] Errore stato abbonamento: {e}")
            return {"active": False, "reason": str(e)}

    def handle_webhook_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Process a Stripe webhook event."""
        event_type = event.get("type", "")
        data = event.get("data", {}).get("object", {})

        if event_type == "checkout.session.completed":
            logger.info(f"[STRIPE] ✅ Checkout completato: {data.get('id')}")
            return {"handled": True, "action": "checkout_completed"}

        elif event_type == "customer.subscription.updated":
            logger.info(f"[STRIPE] 🔄 Abbonamento aggiornato: {data.get('id')}")
            return {"handled": True, "action": "subscription_updated"}

        elif event_type == "customer.subscription.deleted":
            logger.info(f"[STRIPE] ⚠️ Abbonamento cancellato: {data.get('id')}")
            return {"handled": True, "action": "subscription_cancelled"}

        elif event_type == "invoice.payment_failed":
            logger.warning(f"[STRIPE] ❌ Pagamento fallito: {data.get('id')}")
            return {"handled": True, "action": "payment_failed"}

        return {"handled": False, "event_type": event_type}


# Global singleton
payment_service = PaymentService()
