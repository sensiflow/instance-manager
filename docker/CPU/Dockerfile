#CPU
FROM anibali/pytorch:2.0.0-nocuda-ubuntu22.04

RUN git clone https://github.com/ultralytics/yolov5.git && \
    cp -r yolov5/* . && \
    pip install -r requirements.txt

RUN sudo apt-get update \
    && sudo apt-get install -y ffmpeg

RUN curl -sSL https://install.python-poetry.org | python3 -

COPY . .

RUN $HOME/.local/bin/poetry shell && $HOME/.local/bin/poetry install