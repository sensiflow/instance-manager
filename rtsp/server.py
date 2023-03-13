import rtsp.helpers as h


class Rtsp:

    def __init__(self, url):
        self.url = url
        print("Example constructor: " + url)

    def run(self):
        h.rtsp_run(self.url)
