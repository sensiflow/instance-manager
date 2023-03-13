"""Project entry point"""
import rtsp.server as rtsp
import rtsp.constants as const


def run():
    """
        Project Entry point
    """
    rtsp_server = rtsp.Rtsp(const.RTSP_URL_EXAMPLE)
    rtsp.run(rtsp_server)


if __name__ == "__main__":
    run()
