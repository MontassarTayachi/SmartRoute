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
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                }
                for job in jobs
            ],
        }



logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for scheduling periodic tasks."""

    def __init__(self):
        """Initialize scheduler service."""
        self.scheduler = AsyncIOScheduler()
        self.mission_generation_job = None

    def start(self):
        """Start the scheduler."""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")

    def shutdown(self):
        """Shutdown the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shutdown")

    def add_daily_mission_generation(
        self,
        job_func,
        hour: int = 0,
        minute: int = 0,
    ):
        """
        Add a daily job for mission generation.

        Args:
            job_func: Async function to execute for mission generation
            hour: Hour to run (default 0 for midnight)
            minute: Minute to run (default 0)
        """
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

        logger.info(
            f"Scheduled daily mission generation at {hour:02d}:{minute:02d}"
        )

    def remove_mission_generation_job(self):
        """Remove the mission generation job."""
        if self.mission_generation_job:
            self.mission_generation_job.remove()
            self.mission_generation_job = None
            logger.info("Mission generation job removed")

    def get_job_status(self) -> dict[str, any]:
        """
        Get the status of scheduled jobs.

        Returns:
            Dictionary with job status information
        """
        jobs = self.scheduler.get_jobs()
        return {
            "scheduler_running": self.scheduler.running,
            "jobs": [
                {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                }
                for job in jobs
            ],
        }
