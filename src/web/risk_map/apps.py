from django.apps import AppConfig


class RiskMapConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "risk_map"

    def ready(self):
        import os
        import sys
        # En développement avec runserver, Django crée 2 processus :
        #   - reloader (RUN_MAIN absent) : on saute
        #   - processus principal (RUN_MAIN=true) : on démarre
        # En production (gunicorn / Railway) : RUN_MAIN est absent AUSSI,
        #   mais "runserver" n'est pas dans argv → on démarre quand même
        if "runserver" in sys.argv and os.environ.get("RUN_MAIN") != "true":
            return
        try:
            from . import scheduler
            scheduler.start()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Scheduler non démarré : {e}")
