import os
import sys

from Services.CupsService import CupsService
from Services.NextCloudService import NextCloudService
from Services.StdOutService import StdOutService


class SchedulerService:

    def __init__(self):
        self.next_cloud_service = NextCloudService(sys.argv[1], sys.argv[2], sys.argv[3])
        self.cups_service = CupsService()
        self.counter = 0

    def run(self):
        StdOutService.print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        StdOutService.print("checking photos \"in_progress\"")
        photos = self.next_cloud_service.get_photos()
        if len(photos) > 0:
            printer = self.cups_service.get_printer("DI-RS1")

            StdOutService.print("found " + str(len(photos)) + " photos")
            for photo in photos:
                StdOutService.print("============================================================")
                StdOutService.print("found file: " + photo.full_path)
                StdOutService.print("download")
                local_path = self.next_cloud_service.download_photo(photo.user_path)
                if self.next_cloud_service.is_image(local_path):
                    StdOutService.print("rotate image")
                    self.next_cloud_service.rotate_image(local_path)
                    StdOutService.print("crop image")
                    self.next_cloud_service.crop_image(local_path)
                    StdOutService.print("send file to printer: " + local_path)
                    self.cups_service.send_print(printer, local_path)
                else:
                    StdOutService.print("not an image")
                StdOutService.print("remove local copy")
                os.remove(local_path)
                StdOutService.print("move to done folder")
                self.next_cloud_service.move_photo(photo.user_path)
                StdOutService.print("============================================================\n")
            self.counter += len(photos)
        else:
            StdOutService.print("no new photos to print")

        StdOutService.print("photos printed since last restart:" + str(self.counter))
        StdOutService.print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")

    def run_once(self):
        self.run()
