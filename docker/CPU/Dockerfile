#CPU
FROM anibali/pytorch:2.0.0-nocuda-ubuntu22.04

RUN git clone https://github.com/ultralytics/yolov5.git && \
    cp -r yolov5/* . && \
    pip install -r requirements.txt


RUN sudo apt-get update \
    && sudo apt-get install -y ffmpeg
# Install poetry and add it to the path
RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/home/user/.local/bin:$PATH"
ENV PATH="${PATH}:/root/.local/share/pypoetry/venv/bin"

COPY . .

RUN poetry install