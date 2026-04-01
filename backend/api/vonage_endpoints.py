"""
MedicoAssist.it — Vonage Webhook Endpoints
FastAPI routes for Vonage Voice API webhooks.
"""

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
import logging
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/vonage", tags=["Vonage Webhooks"])


@router.get("/answer")
async def handle_answer(request: Request):
    """
    Vonage Answer webhook — called when inbound call connects.
    Returns NCCO (Nexmo Call Control Object) with Italian greeting.
    """
    params = dict(request.query_params)
    caller = params.get("from", "sconosciuto")
    call_uuid = params.get("uuid", "")

    logger.info(f"[VONAGE] 📞 Chiamata in arrivo da {caller} (UUID: {call_uuid})")

    # Build Italian greeting NCCO
    practice_name = os.getenv("PRACTICE_NAME", "MedicoAssist")
    ws_url = os.getenv("VONAGE_WEBHOOK_BASE_URL", "").replace("https://", "wss://")

    ncco = [
        {
            "action": "talk",
            "text": f"Buongiorno, benvenuto allo studio {practice_name}. "
                    f"Sono Anna, l'assistente virtuale. Come posso aiutarla oggi?",
            "language": "it-IT",
            "style": 0,
            "bargeIn": True,
        },
    ]

    # Add WebSocket connection if configured
    if ws_url:
        ncco.append({
            "action": "connect",
            "endpoint": [
                {
                    "type": "websocket",
                    "uri": f"{ws_url}/api/vonage/ws",
                    "content-type": "audio/l16;rate=16000",
                    "headers": {
                        "call_uuid": call_uuid,
                        "caller": caller,
                    },
                }
            ],
        })

    return JSONResponse(content=ncco)


@router.post("/event")
async def handle_event(request: Request):
    """Vonage Event webhook — called for call status updates."""
    try:
        data = await request.json()
        status = data.get("status", "unknown")
        call_uuid = data.get("uuid", "")

        if status in ("completed", "failed", "rejected", "busy", "timeout"):
            logger.info(f"[VONAGE] 📱 Chiamata {call_uuid}: {status}")

            # Log call completion
            if status == "completed":
                duration = data.get("duration", "0")
                logger.info(f"[VONAGE] ✅ Chiamata completata — durata: {duration}s")

        return JSONResponse(content={"status": "ok"})
    except Exception as e:
        logger.error(f"[VONAGE] Errore evento: {e}")
        return JSONResponse(content={"status": "error"}, status_code=200)


@router.post("/fallback")
async def handle_fallback(request: Request):
    """Vonage Fallback webhook — called when primary answer URL fails."""
    logger.warning("[VONAGE] ⚠️ Fallback attivato — risposta di emergenza")

    ncco = [
        {
            "action": "talk",
            "text": "Mi scusi, al momento il servizio non è disponibile. "
                    "La preghiamo di richiamare più tardi. Arrivederci.",
            "language": "it-IT",
            "style": 0,
        },
    ]
    return JSONResponse(content=ncco)


@router.websocket("/ws")
async def vonage_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for Vonage audio streaming.
    Receives audio from phone calls and streams to Gemini for processing.
    """
    await websocket.accept()
    logger.info("[VONAGE] 🔌 WebSocket connesso")

    try:
        # Get call metadata from headers
        headers = dict(websocket.headers)
        call_uuid = headers.get("call_uuid", "unknown")

        while True:
            # Receive audio data from Vonage
            data = await websocket.receive_bytes()

            # Process audio through Gemini bridge
            try:
                from services.vonage_realtime_bridge import VonageRealtimeBridge
                bridge = VonageRealtimeBridge()
                response = await bridge.process_audio(call_uuid, data)

                if response:
                    # Send audio response back to Vonage
                    await websocket.send_bytes(response)
            except ImportError:
                pass  # Bridge not available yet
            except Exception as e:
                logger.error(f"[VONAGE] Errore elaborazione audio: {e}")

    except WebSocketDisconnect:
        logger.info("[VONAGE] 🔌 WebSocket disconnesso")
    except Exception as e:
        logger.error(f"[VONAGE] Errore WebSocket: {e}")
