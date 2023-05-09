from abc import ABC, abstractmethod


class StreamerInterface(ABC):
    @abstractmethod
    def start_stream(self):
        pass

    @abstractmethod
    def stop_stream(self):
        pass

    @abstractmethod
    def next_frame(self, frame):
        pass
