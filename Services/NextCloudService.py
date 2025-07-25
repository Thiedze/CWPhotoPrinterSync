import os.path
from datetime import datetime

from PIL import Image
from nc_py_api import Nextcloud


class NextCloudService:

    def __init__(self, url, username, password):
        self.next_cloud_service = Nextcloud(nextcloud_url=url, nc_auth_user=username, nc_auth_pass=password)
        self.in_progress_folder_path = "in_progress"

    def get_photos(self):
        return self.next_cloud_service.files.listdir("/Photos/Input")

    def download_photo(self, path):
        with open(os.path.join(self.in_progress_folder_path, os.path.basename(path)), 'wb') as file:
            file.write(self.next_cloud_service.files.download(path))
        return os.path.join(self.in_progress_folder_path, os.path.basename(path))

    def move_photo(self, user_path):
        filename = os.path.basename(user_path)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        destination_path = os.path.join("/Photos/Done", timestamp + "_" + filename)

        self.next_cloud_service.files.move(user_path, destination_path)

    @staticmethod
    def is_image(file_path):
        try:
            with Image.open(file_path) as image:
                image.verify()
            return True
        except Exception:
            return False

    @staticmethod
    def crop_image(file_path):
        with Image.open(file_path) as image:
            target_cm = (10, 15)
            dpi = 300

            target_px = (int(target_cm[0] / 2.54 * dpi), int(target_cm[1] / 2.54 * dpi))
            target_ratio = target_px[0] / target_px[1]

            width, height = image.size
            current_ratio = width / height

            if current_ratio > target_ratio:
                new_width = int(height * target_ratio)
                left = (width - new_width) // 2
                box = (left, 0, left + new_width, height)
            else:
                new_height = int(width / target_ratio)
                top = (height - new_height) // 2
                box = (0, top, width, top + new_height)

            cropped = image.crop(box)
            resized = cropped.resize(target_px, Image.LANCZOS)

            resized.save(file_path, dpi=(dpi, dpi))

    @staticmethod
    def rotate_image(file_path):
        with Image.open(file_path) as image:
            width, height = image.size
            if width > height:
                image = image.rotate(270, expand=True)
            image.save(file_path)

    @staticmethod
    def concatenate_images(folder, left_file, right_file):
        left_image = Image.open(os.path.join(folder, left_file))
        right_image = Image.open(os.path.join(folder, right_file))

        concatenate_image = Image.new('RGB', (left_image.width + right_image.width, left_image.height))
        concatenate_image.paste(left_image, (0, 0))
        concatenate_image.paste(right_image, (left_image.width, 0))
        concatenate_image.save(os.path.join(folder, left_file + right_file))
        concatenate_image.close()
        return os.path.join(folder, left_file + right_file)


    def reset_in_progress(self, photos):
        for photo in photos:
            self.next_cloud_service.files.delete(photo.user_path)

