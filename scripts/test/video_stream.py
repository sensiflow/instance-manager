import cv2
import subprocess as sp
import argparse

"""
This script is used to stream video from a file to an RTSP server in loop.
Can be useful to test the instance manager workers.
"""
parser = argparse.ArgumentParser(description='Webcam streamer')
parser.add_argument('--host', type=str, default='localhost',
                    help='Host IP address',)
parser.add_argument('--port', type=int, default=8554,
                    help='Host port number', required=False)
parser.add_argument('--path', type=str, default='video',
                    help='Stream path', required=False)
parser.add_argument('--file', type=str, help='Video file path', required=True)
print("possible cmd line args: --host, --port, --path")
args = parser.parse_args()

stream_url = f"rtsp://{args.host}:{args.port}/{args.path}"
video_file = args.file


def start():
    try:
        cap = cv2.VideoCapture(video_file)
        # Get video frames width
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        # Get video frames height
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))  # Get video framerate

        print(
            f"Video width: {width}\nVideo height: {height}\nVideo FPS: {fps}")
        command = ['ffmpeg',
                   '-re',
                   '-stream_loop', '-1',
                   '-i', video_file,
                   '-c:v', 'copy',
                   '-c:a', 'copy',
                   '-f', 'rtsp',
                   '-y',
                   '-rtsp_transport', 'tcp',
                   stream_url]
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
        start()


if __name__ == "__main__":
    start()
