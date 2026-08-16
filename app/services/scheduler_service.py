import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for scheduling periodic tasks using a background thread."""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.mission_generation_job = None

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shutdown")

    def add_daily_mission_generation(self, job_func, hour: int = 0, minute: int = 0):
        if self.mission_generation_job:
            logger.warning("Mission generation job already exists, removing it")
            self.mission_generation_job.remove()

        self.mission_generation_job = self.scheduler.add_job(
            job_func,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="daily_mission_generation",
            name="Daily Mission Generation",
            replace_existing=True,
        )
        logger.info(f"Scheduled daily mission generation at {hour:02d}:{minute:02d}")

    def remove_mission_generation_job(self):
        if self.mission_generation_job:
            self.mission_generation_job.remove()
            self.mission_generation_job = None
            logger.info("Mission generation job removed")

    def get_job_status(self) -> dict:
        jobs = self.scheduler.get_jobs()
        return {
            "scheduler_running": self.scheduler.running,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": (
                        job.next_run_time.isoformat()
                        if getattr(job, "next_run_time", None)
                        else None
                    ),
                }
                for job in jobs
            ],
        }
