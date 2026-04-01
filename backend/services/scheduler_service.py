"""
MedicoAssist.it — Scheduler Service
Background job scheduler for automated tasks:
- Promemoria appuntamenti (appointment reminders)
- Pulizia sessioni scadute (session cleanup)
- Report giornalieri (daily reports)
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any

logger = logging.getLogger(__name__)


class SchedulerService:
    """Background task scheduler for MedicoAssist automations."""

    def __init__(self):
        self.tasks: Dict[str, asyncio.Task] = {}
        self.running = False

    async def start(self):
        """Start the scheduler with all configured jobs."""
        if self.running:
            logger.warning("[SCHEDULER] Già in esecuzione")
            return

        self.running = True
        logger.info("[SCHEDULER] ✅ Avviato")

        # Schedule recurring jobs
        self.tasks["promemoria"] = asyncio.create_task(
            self._run_periodic("promemoria", self._send_appointment_reminders, interval_hours=1)
        )
        self.tasks["pulizia_sessioni"] = asyncio.create_task(
            self._run_periodic("pulizia_sessioni", self._cleanup_expired_sessions, interval_hours=6)
        )
        self.tasks["keep_alive"] = asyncio.create_task(
            self._run_periodic("keep_alive", self._db_keep_alive, interval_hours=4)
        )

    async def stop(self):
        """Stop all scheduled tasks."""
        self.running = False
        for name, task in self.tasks.items():
            task.cancel()
            logger.info(f"[SCHEDULER] Task '{name}' fermato")
        self.tasks.clear()
        logger.info("[SCHEDULER] ⏹ Arrestato")

    async def _run_periodic(self, name: str, func: Callable, interval_hours: float):
        """Run a function periodically."""
        interval_seconds = interval_hours * 3600
        while self.running:
            try:
                await func()
            except Exception as e:
                logger.error(f"[SCHEDULER] Errore in '{name}': {e}")
            await asyncio.sleep(interval_seconds)

    # ================================================================
    # Scheduled Jobs
    # ================================================================

    async def _send_appointment_reminders(self):
        """Send reminders for tomorrow's appointments."""
        try:
            from database import get_supabase_admin
            supabase = get_supabase_admin()
            if not supabase:
                return

            tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
            response = (
                supabase.table("appointments")
                .select("*, patients(*)")
                .eq("data_appuntamento", tomorrow)
                .eq("stato", "confermato")
                .execute()
            )

            appointments = response.data or []
            if not appointments:
                return

            logger.info(f"[SCHEDULER] Invio {len(appointments)} promemoria per {tomorrow}")

            for appt in appointments:
                patient = appt.get("patients", {})
                email = patient.get("email")
                if email:
                    try:
                        from services.email_service import EmailService
                        email_service = EmailService()
                        await email_service.send_promemoria(
                            to_email=email,
                            paziente_nome=patient.get("nome", ""),
                            data=appt.get("data_appuntamento", ""),
                            ora=appt.get("ora_appuntamento", ""),
                            prestazione=appt.get("prestazione", ""),
                        )
                    except Exception as e:
                        logger.error(f"[SCHEDULER] Errore invio promemoria: {e}")

        except Exception as e:
            logger.error(f"[SCHEDULER] Errore promemoria: {e}")

    async def _cleanup_expired_sessions(self):
        """Clean up expired webhook sessions and stale data."""
        try:
            # Clean up old conversation sessions (>24h)
            from database import get_supabase_admin
            supabase = get_supabase_admin()
            if not supabase:
                return

            cutoff = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            supabase.table("conversations").update(
                {"stato": "scaduta"}
            ).eq("stato", "in_corso").lt("inizio", cutoff).execute()

            logger.info("[SCHEDULER] ✅ Sessioni scadute pulite")
        except Exception as e:
            logger.error(f"[SCHEDULER] Errore pulizia sessioni: {e}")

    async def _db_keep_alive(self):
        """
        Periodic DB keep-alive to prevent Supabase idle disconnects.
        Critical for free-tier Supabase projects.
        """
        try:
            from database import get_supabase_admin
            supabase = get_supabase_admin()
            if supabase:
                supabase.table("practices").select("id").limit(1).execute()
                logger.info("[SCHEDULER] 💓 DB keep-alive OK")
        except Exception as e:
            logger.error(f"[SCHEDULER] Errore keep-alive: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        return {
            "running": self.running,
            "active_tasks": list(self.tasks.keys()),
            "task_count": len(self.tasks),
        }


# Global singleton
scheduler_service = SchedulerService()
