class StdOutService:

    @staticmethod
    def print(message):
        print(message)
        with open("log.txt", "a") as f:
            f.write(message + "\n")
