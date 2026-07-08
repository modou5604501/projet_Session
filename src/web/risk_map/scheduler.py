"""
Scheduler APScheduler — mise à jour automatique hebdomadaire des données.
"""

import sys
import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

# Ajouter le dossier preprocessing au path
PREPROCESSING_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "preprocessing"
)
if PREPROCESSING_DIR not in sys.path:
    sys.path.insert(0, os.path.abspath(PREPROCESSING_DIR))


def refresh_job():
    """Tâche planifiée : importe les nouvelles bornes depuis Données Québec."""
    try:
        from refresh_data import run_refresh
        result = run_refresh()
        logger.info(f"Refresh planifié terminé : {result}")
    except Exception as e:
        logger.error(f"Erreur refresh planifié : {e}")


_scheduler = None


def start():
    global _scheduler
    if _scheduler is not None:
        return

    _scheduler = BackgroundScheduler(timezone="America/Montreal")
    _scheduler.add_job(
        refresh_job,
        trigger=IntervalTrigger(weeks=1),
        id="weekly_refresh",
        name="Mise à jour bornes Données Québec",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("Scheduler démarré — refresh hebdomadaire activé")


def stop():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown()
        _scheduler = None
