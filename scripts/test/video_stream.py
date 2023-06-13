import cv2
import subprocess as sp
import argparse

"""
This script is used to stream video from a file to an RTSP server in loop.
Can be useful to test the instance manager workers.
"""
parser = argparse.ArgumentParser(description='Webcam streamer')
parser.add_argument('--host', type=str, default='localhost', help='Host IP address',)
parser.add_argument('--port', type=int, default=8554, help='Host port number', required=False)
parser.add_argument('--path', type=str, default='video', help='Stream path', required=False)
print("possible cmd line args: --host, --port, --path")
args = parser.parse_args()
stream_url = f"rtsp://{args.host}:{args.port}/{args.path}"

video_file = "path/to/video.mp4"

cap = cv2.VideoCapture(video_file)

width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))  # Get video frames width
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))  # Get video frames height
fps = int(cap.get(cv2.CAP_PROP_FPS))  # Get video framerate

print(f"Video width: {width}\nVideo height: {height}\nVideo FPS: {fps}")

command = ['ffmpeg',
           '-re',
           '-stream_loop', '-1',
           '-y',
           '-i', video_file,
           '-c', 'copy',
           '-f', 'rtsp',
           '-rtsp_transport', 'tcp',
           '-muxdelay', '0.1',
           stream_url]

try:
    p = sp.Popen(command, stdin=sp.PIPE)

    while (cap.isOpened()):
        ret, frame = cap.read()

        if not ret:
            # Reset video to the beginning if it reaches the end
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        p.stdin.write(frame.tobytes())
finally:
    p.stdin.close()  # Close stdin pipe
    p.wait()  # Wait for FFmpeg sub-process to finish
    cap.release()
