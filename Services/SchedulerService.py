import os
import sys

from Services.CupsService import CupsService
from Services.NextCloudService import NextCloudService


class SchedulerService:

    def __init__(self):
        self.next_cloud_service = NextCloudService(sys.argv[1], sys.argv[2])
        self.cups_service = CupsService()

    def run(self):
        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        print("checking photos \"in_progress\"")
        photos = self.next_cloud_service.get_photos()
        if len(photos) > 0:
            printer = self.cups_service.get_printer("DI-RS1")

            for photo in photos:
                print("==========================================================")
                print("found file: " + photo.full_path)
                print("download")
                local_path = self.next_cloud_service.download_photo(photo.user_path)
                if self.next_cloud_service.is_image(local_path):
                    print("crop image")
                    self.next_cloud_service.crop_image(local_path)
                    print("send file to printer: " + local_path)
                    self.cups_service.send_print(printer, local_path)
                else:
                    print("not an image")
                print("remove local copy")
                os.remove(local_path)
                print("move to done folder")
                self.next_cloud_service.move_photo(photo.user_path)
                print("==========================================================\n")
        else:
            print("no new photos to print")

        print("++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")

    def run_once(self):
        self.run()
