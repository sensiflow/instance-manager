# image-processor

This is the image processor module for the Sensiflow system.

## Getting Started

### Prerequisites

Have poetry installed.
Have python 3.8 installed.

### Installing

### Running the application

This component is comprised of two executables
Each executable has the capacity to receive an argument, the ENVIRONMENT name, which dictates the config to use

- `run-instance-manager.bat`/`run-instance-manager.sh`
- `run-scheduler.bat`/`run-scheduler.sh`

These can be ran inside a poetry shell.

#### Instruction to run the executables

Open a cmd/terminal , run `poetry shell` and run the executable.

### Configs

At least two configs are required:

The first one is the config file for the image processor. This file is located at `./config/worker.ini`, its name must be worker.ini and it is used to configure the image processor.
The second one is the config file for the instance manager.

The elements that are required are marked with an asterisk.
The optional elements are marked with a question mark.
Format of the instance manager config file:

```ini
[DATABASE]
host = *
port = *
user = *
password = *

[RABBITMQ]
HOST= *
PORT= *
USER= *
PASSWORD= *
INSTANCE_CONTROLLER_QUEUE= *
ACK_DEVICE_STATUS_QUEUE= *
ACK_DEVICE_DELETE_QUEUE= *


[HARDWARE_ACCELERATION]
PROCESSING_MODE= * # Could be either GPU or CPU
CUDA_VERSION= *  # Not necessary if PROCESSING_MODE=CPU
```

Format of the worker config file:

```ini
[DATABASE]
HOST= *
PORT= *
USER= *
PASSWORD= *

[MEDIA_SERVER]
DESTINATION_HOST = *
WRITE_USER = *
WRITE_PASSWORD = *
RTSP_PORT = *
RTSPS_PORT = *
SECURE = ? # Default: False


```

#### Media Server Authentication

This process is handled by the image processor.
The credentials are configured in the config file `./config/worker.ini` under the section.


#### Test scripts

The repository contains some test scripts to create virtual cameras from webcams or even video files.

To run the test scripts it is required to have ffmpeg installed. Download it [here](https://ffmpeg.org/download.html)

Some test scripts for streaming camera / video feed to the media server can be found at `./scripts/test/`.

These scripts can take the following arguments:
- host: The host of the media server. It can be either an IP address or a domain name.
- Safe: If set to True, the script will use HTTPS to stream the video feed. If set to False, the script will use HTTP. Notice that the media server must be configured to use HTTPS.
- path: The path to the video feed.

If the media server is using user and password authentication the url must follow the format:

```
rtsp://user:password@host:port/path
```

Example usages of the test scripts:

```bash
python webcam_stream.py --host=admin:admin@localhost --Safe=True --path=test 
```
