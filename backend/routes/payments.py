"""MedicoAssist.it — Payments Routes (Pagamenti)"""

from fastapi import APIRouter, Depends, HTTPException, Request
from auth import get_current_active_user
import os

router = APIRouter(prefix="/api/payments", tags=["Pagamenti"])


@router.get("/plans")
def get_plans():
    """Get available subscription plans."""
    return {
        "plans": [
            {
                "id": "basic",
                "nome": "Base",
                "prezzo_mensile": 49.0,
                "valuta": "EUR",
                "features": [
                    "Assistente AI per telefono",
                    "Fino a 100 chiamate/mese",
                    "Dashboard base",
                ],
            },
            {
                "id": "pro",
                "nome": "Professionale",
                "prezzo_mensile": 99.0,
                "valuta": "EUR",
                "features": [
                    "Chiamate illimitate",
                    "Gestione appuntamenti completa",
                    "Integrazione agenda",
                    "Report e statistiche",
                ],
            },
            {
                "id": "enterprise",
                "nome": "Enterprise",
                "prezzo_mensile": None,
                "valuta": "EUR",
                "features": [
                    "Multi-studio",
                    "API personalizzate",
                    "Supporto dedicato",
                    "SLA garantito",
                ],
            },
        ]
    }


@router.post("/create-checkout-session")
def create_checkout_session(plan_id: str, current_user=Depends(get_current_active_user)):
    """Create a Stripe checkout session."""
    try:
        import stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not stripe.api_key:
            raise HTTPException(status_code=503, detail="Pagamenti non configurati")

        # Map plan to Stripe price
        price_map = {
            "basic": os.getenv("STRIPE_PRICE_BASIC"),
            "pro": os.getenv("STRIPE_PRICE_PRO"),
        }

        price_id = price_map.get(plan_id)
        if not price_id:
            raise HTTPException(status_code=400, detail="Piano non valido")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=os.getenv("FRONTEND_URL", "http://localhost:3000") + "/dashboard?payment=success",
            cancel_url=os.getenv("FRONTEND_URL", "http://localhost:3000") + "/pricing?payment=cancelled",
        )
        return {"checkout_url": session.url}
    except ImportError:
        raise HTTPException(status_code=503, detail="Modulo stripe non installato")


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    try:
        import stripe
        payload = await request.body()
        sig = request.headers.get("stripe-signature")
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

        if webhook_secret and sig:
            event = stripe.Webhook.construct_event(payload, sig, webhook_secret)
        else:
            import json
            event = json.loads(payload)

        event_type = event.get("type", "")
        if event_type == "checkout.session.completed":
            print(f"[STRIPE] ✅ Pagamento completato: {event.get('data', {}).get('object', {}).get('id')}")
        elif event_type == "customer.subscription.deleted":
            print(f"[STRIPE] ⚠️ Abbonamento cancellato")

        return {"received": True}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
