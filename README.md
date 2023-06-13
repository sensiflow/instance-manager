# image-processor

Image Processor for Sensi App

This is the image processor for the Sensi App.

// TODO: Add more information about the project
// Enumerate the sections of the README

## Getting Started

#### Test scripts

Some test scripts for streaming camera / video feed to the media server can be found at `./scripts/test/`.

If the media server is using user and password authentication the url must follow the format:

```
rtsp://user:password@host:port/path
```

Example usages of the test scripts:

```bash
python webcam_stream.py --host=admin:admin@localhost --Safe=True --path=test 
```


### Prerequisites

### Installing

### Running the tests

### Running the application




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

Format of the image processor config file:

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