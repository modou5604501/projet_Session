from django.apps import AppConfig


class RiskMapConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "risk_map"

    def ready(self):
        # Démarrer le scheduler uniquement dans le processus principal
        import os
        if os.environ.get("RUN_MAIN") != "true":
            return
        try:
            from . import scheduler
            scheduler.start()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Scheduler non démarré : {e}")
