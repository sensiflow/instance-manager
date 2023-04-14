#CPU
FROM anibali/pytorch:2.0.0-nocuda-ubuntu22.04

RUN git clone https://github.com/ultralytics/yolov5.git && \
    cp -r yolov5/* . && \
    pip install -r requirements.txt

COPY src/image_processor/transmit.py ./app/transmit.py

RUN sudo apt-get update && sudo apt-get install ffmpeg libsm6 libxext6  -y
