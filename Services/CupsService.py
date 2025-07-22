import cups


class CupsService:

    def __init__(self):
        self.connection = cups.Connection()

    def get_printer(self, name):
        printers = self.connection.getPrinters()
        for printer in printers:
            if printer == name:
                return printer
        return None

    def send_print(self, printer, photo_path):
        self.connection.printFile(printer, photo_path, "Fotoauftrag", {})
