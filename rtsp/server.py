"""Example module"""
import dataclasses
import rtsp.helpers as h



@dataclasses.dataclass
class Rtsp:
    """
        Example class
    """
    url: str


def run(rtsp_server: Rtsp) -> None:
    """
        Example function
    """
    h.rtsp_run(rtsp_server.url)
