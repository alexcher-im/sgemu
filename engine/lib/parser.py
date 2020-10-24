class LineFeeder:
    def __init__(self, parts):
        self.parts = parts
        self.number = 0

    def read(self) -> str:
        return self.parts[self.number]

    def pop(self) -> str:
        text = self.parts[self.number]
        self.number += 1
        return text

    def back(self):
        if self.number != 0:
            self.number -= 1

    def __iter__(self):
        return self

    def __next__(self):
        try:
            return self.pop()
        except IndexError:
            raise StopIteration


def startswith_poll(parts, phrases, result=lambda x, y: None, stop=None, all_poll=lambda line: None):
    for line in parts:
        for phrase in phrases:
            if line.strip().lower().startswith(phrase):
                result(phrase, phrases[phrase](parts, line))
            all_poll(line)
            if line.strip().lower() == stop:
                return stop
