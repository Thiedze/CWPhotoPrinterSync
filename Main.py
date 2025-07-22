import sys
import time

import schedule

from Services.SchedulerService import SchedulerService

if __name__ == "__main__":
    scheduler_service = SchedulerService()
    schedule.every(1).minutes.do(scheduler_service.run)

    scheduler_service.run_once()

    while True:
        schedule.run_pending()
        time.sleep(1)
