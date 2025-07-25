class StdOutService:

    @staticmethod
    def print(message, app=None):
        print(message)
        with open("log.txt", "a") as f:
            f.write(message + "\n")
        if app:
            app.logger.info(message)