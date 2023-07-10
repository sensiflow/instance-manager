"""
This script is used to stream webcam video to an RTSP server.
This can be as a live video stream.
"""

import cv2
import subprocess as sp
import argparse

parser = argparse.ArgumentParser(description='Webcam streamer')
parser.add_argument('--host', type=str, default='localhost', help='Host IP address',)
parser.add_argument('--safe', type=bool, default=False, help='Host port number', required=False)
parser.add_argument('--path', type=str, default='webcam', help='Stream path', required=False)
print("possible cmd line args: --host, --safe, --path")
args = parser.parse_args()

if(args.safe == False):
    stream_url = f"rtsp://{args.host}:8554/{args.path}"
else:
    stream_url = f"rtsps://{args.host}:8322/{args.path}"

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
           stream_url]

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
