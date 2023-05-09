#GPU
ARG CUDA_VERSION
FROM anibali/pytorch:2.0.0-${CUDA_VERSION}-ubuntu22.04

RUN git clone https://github.com/ultralytics/yolov5.git && \
    cp -r yolov5/* . && \
    pip install -r requirements.txt

RUN sudo apt-get update \
    && sudo apt-get install -y ffmpeg


COPY ./docker/scripts/ ./