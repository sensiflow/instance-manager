"""
This script is used to stream webcam video to an RTSP server.
This can be as a live video stream.
"""

import cv2
import subprocess as sp

rtsp_url = "rtsp://localhost:8554/webcam"

cap = cv2.VideoCapture(0)

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # Get video frames width
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # Get video frames height
fps = int(cap.get(cv2.CAP_PROP_FPS))  # Get video framerate

print(f"Video width: {width}\nVideo height: {height}\nVideo FPS: {fps}")

command = ['ffmpeg',
           '-re',
           '-stream_loop', '-1',
           '-y',
           '-f', 'rawvideo',
           '-vcodec', 'rawvideo',
           '-pix_fmt', 'bgr24',
           '-s', "{}x{}".format(width, height),
           '-r', str(fps if fps > 0 else 24),
           '-i', '-',
           '-c', 'h264',
           '-preset', 'ultrafast',
           '-f', 'rtsp',
           '-rtsp_transport', 'tcp',
           '-muxdelay', '0.1',
           rtsp_url]

try:
    p = sp.Popen(command, stdin=sp.PIPE)

    while (cap.isOpened()):
        ret, frame = cap.read()

        if not ret:
            break

        p.stdin.write(frame.tobytes())
finally:
    p.stdin.close()  # Close stdin pipe
    p.wait()  # Wait for FFmpeg sub-process to finish
    cap.release()
