import subprocess

from src.image_processor.streamer_interface import StreamerInterface


class StreamerRTSP(StreamerInterface):

    def __init__(self,
                 destination_uri: str,
                 width: int, height: int,
                 framerate: int = 30):
        self.proc = None
        self.pipe = None
        self.destination_uri = destination_uri
        self.width = width
        self.height = height
        self.framerate = framerate
        self.isClosed = False

    def start_stream(self):
        if self.proc is not None:
            raise Exception("Streamer already started")
        command = [
            'ffmpeg',
            '-stats',
            '-re',
            '-stream_loop', '-1',
            '-f', 'rawvideo',
            # because we dont know what type of codec the input will be
            '-vcodec', 'rawvideo',
            '-pix_fmt', 'bgr24',  # -pix_fmt bgr24 # needed because openCV
            '-s', "{}x{}".format(self.width, self.height),
            '-r', str(self.framerate),
            '-i', '-',
            '-c', 'libx264',  # https://trac.ffmpeg.org/wiki/Encode/H.264
            '-preset', 'ultrafast',
            '-f', 'rtsp',
            '-rtsp_transport', 'tcp',
            self.destination_uri
        ]
        self.proc = subprocess.Popen(command, stdin=subprocess.PIPE)
        self.pipe = self.proc.stdin

    def next_frame(self, frame):
        """Receives the frame object and sends it to the streaming process."""
        if self.isClosed:
            raise Exception("Streamer already closed")
        if not self.has_started:
            raise Exception("Streamer not started")

        self.pipe.write(frame.tobytes())
        self.pipe.flush()

    def stop_stream(self):
        if self.isClosed:
            raise Exception("Streamer already closed")
        if not self.has_started:
            raise Exception("Streamer not started")

        self.isClosed = True
        self.pipe.close()
        self.proc.wait()

    def is_streaming(self):
        """TODO:Sque tirar ?
        Returns True if the streaming process is running."""
        pass

    def has_started(self):
        if self.pipe is None:
            return False
        return True
