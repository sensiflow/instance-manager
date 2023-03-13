import rtsp.server as rtsp
import rtsp.constants as const

# Triggers the entire project

def run():
    rtsp_server = rtsp.Rtsp(const.RTSP_URL_EXAMPLE)
    rtsp_server.run()

# Entry point
if __name__ == "__main__":
    run()