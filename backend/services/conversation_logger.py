"""
MedicoAssist.it — Conversation Logger Service
Logs AI conversations to Supabase for audit, analytics, and GDPR compliance.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ConversationLogger:
    """
    Logs phone conversations between the AI assistant and patients.
    Data is stored in Supabase for GDPR-compliant audit trails.
    """

    def __init__(self, supabase_client=None):
        self.supabase = supabase_client
        self.table = "conversations"
        self.messages_table = "conversation_messages"

    def _get_supabase(self):
        """Lazy Supabase init."""
        if not self.supabase:
            try:
                from database import get_supabase_admin
                self.supabase = get_supabase_admin()
            except Exception as e:
                logger.error(f"Errore connessione Supabase: {e}")
        return self.supabase

    # ================================================================
    # Conversation Lifecycle
    # ================================================================

    async def start_conversation(
        self,
        session_id: str,
        practice_id: str,
        channel: str = "telefono",
        caller_number: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Start a new conversation and return its ID."""
        supabase = self._get_supabase()
        if not supabase:
            logger.warning("Supabase non disponibile — conversazione non registrata")
            return None

        try:
            data = {
                "session_id": session_id,
                "practice_id": practice_id,
                "canale": channel,
                "numero_chiamante": caller_number,
                "stato": "in_corso",
                "inizio": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
            }
            response = supabase.table(self.table).insert(data).execute()
            if response.data:
                conv_id = response.data[0].get("id")
                logger.info(f"[CONV] Conversazione avviata: {conv_id}")
                return conv_id
        except Exception as e:
            logger.error(f"Errore avvio conversazione: {e}")
        return None

    async def end_conversation(
        self,
        conversation_id: str,
        summary: str = "",
        outcome: str = "completata",
        paziente_id: Optional[str] = None,
    ):
        """End a conversation with summary and outcome."""
        supabase = self._get_supabase()
        if not supabase:
            return

        try:
            update_data = {
                "stato": outcome,  # completata, annullata, trasferita, errore
                "fine": datetime.utcnow().isoformat(),
                "riepilogo": summary,
            }
            if paziente_id:
                update_data["paziente_id"] = paziente_id

            supabase.table(self.table).update(update_data).eq("id", conversation_id).execute()
            logger.info(f"[CONV] Conversazione terminata: {conversation_id} ({outcome})")
        except Exception as e:
            logger.error(f"Errore chiusura conversazione: {e}")

    # ================================================================
    # Message Logging
    # ================================================================

    async def log_message(
        self,
        conversation_id: str,
        role: str,  # "paziente", "assistente", "sistema"
        content: str,
        message_type: str = "testo",  # testo, vocale, azione
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log a single message in the conversation."""
        supabase = self._get_supabase()
        if not supabase:
            return

        try:
            data = {
                "conversation_id": conversation_id,
                "ruolo": role,
                "contenuto": content,
                "tipo_messaggio": message_type,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
            }
            supabase.table(self.messages_table).insert(data).execute()
        except Exception as e:
            logger.error(f"Errore registrazione messaggio: {e}")

    async def log_intent(
        self,
        conversation_id: str,
        intent: str,
        confidence: float = 0.0,
        entities: Optional[Dict[str, Any]] = None,
    ):
        """Log a detected intent."""
        await self.log_message(
            conversation_id=conversation_id,
            role="sistema",
            content=f"Intent rilevato: {intent} (confidenza: {confidence:.2f})",
            message_type="azione",
            metadata={
                "intent": intent,
                "confidence": confidence,
                "entities": entities or {},
            },
        )

    async def log_appointment_action(
        self,
        conversation_id: str,
        action: str,  # prenotazione, modifica, annullamento
        appointment_data: Optional[Dict[str, Any]] = None,
    ):
        """Log an appointment-related action."""
        await self.log_message(
            conversation_id=conversation_id,
            role="sistema",
            content=f"Azione appuntamento: {action}",
            message_type="azione",
            metadata={
                "azione_appuntamento": action,
                "dati_appuntamento": appointment_data or {},
            },
        )

    # ================================================================
    # Retrieval
    # ================================================================

    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get a conversation by ID."""
        supabase = self._get_supabase()
        if not supabase:
            return None

        try:
            response = supabase.table(self.table).select("*").eq("id", conversation_id).single().execute()
            return response.data
        except Exception:
            return None

    def get_conversation_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a conversation."""
        supabase = self._get_supabase()
        if not supabase:
            return []

        try:
            response = (
                supabase.table(self.messages_table)
                .select("*")
                .eq("conversation_id", conversation_id)
                .order("timestamp")
                .execute()
            )
            return response.data or []
        except Exception:
            return []

    def get_recent_conversations(
        self, practice_id: str, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get recent conversations for a practice."""
        supabase = self._get_supabase()
        if not supabase:
            return []

        try:
            response = (
                supabase.table(self.table)
                .select("*")
                .eq("practice_id", practice_id)
                .order("inizio", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data or []
        except Exception:
            return []

    # ================================================================
    # Statistics
    # ================================================================

    def get_stats(self, practice_id: str) -> Dict[str, Any]:
        """Get conversation statistics for a practice."""
        supabase = self._get_supabase()
        if not supabase:
            return {}

        try:
            all_convs = (
                supabase.table(self.table)
                .select("*")
                .eq("practice_id", practice_id)
                .execute()
            )
            convs = all_convs.data or []
            total = len(convs)
            completate = sum(1 for c in convs if c.get("stato") == "completata")
            trasferite = sum(1 for c in convs if c.get("stato") == "trasferita")

            return {
                "totale_conversazioni": total,
                "completate": completate,
                "trasferite": trasferite,
                "tasso_risoluzione": round(completate / max(total, 1) * 100, 1),
            }
        except Exception:
            return {}
