import cv2
import subprocess as sp

"""
This script is used to stream video from a file to an RTSP server in loop.
Can be useful to test the instance manager workers.
"""

rtsp_url = "rtsp://localhost:8554/video"
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
           rtsp_url]

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
