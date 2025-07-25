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
        self.single_image_timeout = 10 # X times scan interval

    def run(self):
        printer = self.cups_service.get_printer("DI-RS1")
        StdOutService.print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        StdOutService.print("checking photos \"in_progress\"")
        self.check_single_image_timeout(printer)

        photos = self.next_cloud_service.get_photos()
        if len(photos) > 0:
            self.handle_photos(photos, printer)
            StdOutService.print("============================================================\n")
        else:
            StdOutService.print("no new photos to print")

        StdOutService.print("photos printed since last restart:" + str(self.counter))
        StdOutService.print("+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++\n")

    def run_once(self):
        self.run()

    def handle_photos(self, photos, printer):
        StdOutService.print("found " + str(len(photos)) + " photos")
        for index, photo in enumerate(photos):
            StdOutService.print("============================================================")
            StdOutService.print("found file: " + photo.full_path)
            StdOutService.print("download")
            local_path = self.next_cloud_service.download_photo(photo.user_path)
            if self.next_cloud_service.is_image(local_path):
                StdOutService.print("rotate image")
                self.next_cloud_service.rotate_image(local_path)
                StdOutService.print("crop image")
                self.next_cloud_service.crop_image(local_path)
                StdOutService.print("move to done folder")
                self.next_cloud_service.move_photo(photo.user_path)
        self.counter += len(photos)

        files = [files for files in os.listdir("in_progress")]
        left_file = None
        for index, file in enumerate(files):
            if (index + 1) % 2 == 0:
                right_file = file
                self.concatenate_images(left_file, right_file, printer)
            else:
                left_file = file
        self.single_image_timeout = 10


    def concatenate_images(self, left_file, right_file, printer):
        StdOutService.print("concatenate two images: " + left_file + " and " + right_file)
        local_path = self.next_cloud_service.concatenate_images("in_progress", left_file, right_file)
        StdOutService.print("send file to printer: " + local_path)
        self.cups_service.send_print(printer, local_path)
        StdOutService.print("remove local copy")
        if right_file != left_file:
            os.remove(os.path.join("in_progress", right_file))
        os.remove(os.path.join("in_progress", left_file))
        os.remove(local_path)

    def check_single_image_timeout(self, printer):
        local_photos = [files for files in os.listdir("in_progress")]
        if len(local_photos) > 0:
            self.single_image_timeout -= 1
            if self.single_image_timeout <= 0:
                StdOutService.print("timeout reached, printing in_progress photos")
                self.concatenate_images(local_photos[0], local_photos[0], printer)
                self.single_image_timeout = 10