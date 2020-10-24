class TimingManager:
    def __init__(self):
        self.fps = 0
        self.delay = 0
        self.should_execute = True
        self.tick_count = 0

    def stop(self):
        self.should_execute = False

    def set_fps(self, fps):
        self.fps = fps
        self.delay = 1 / fps

    def run(self, scene):
        pass
