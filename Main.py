import time
import schedule

from Services.SchedulerService import SchedulerService

scheduler_service = SchedulerService()
schedule.every(1).minutes.do(scheduler_service.run)

scheduler_service.run_once()

while True:
    schedule.run_pending()
    time.sleep(1)