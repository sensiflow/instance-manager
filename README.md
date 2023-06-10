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


### Prerequisites

### Installing

### Running the tests

### Running the application




### Configs

At least two configs are required:

The first one is the config file for the image processor. This file is located at `./config/worker.ini`, its name must be worker.ini and it is used to configure the image processor.
The second one is the config file for the instance manager.

Format of the instance manager config file:

```ini
[DATABASE]
host = X
port = X
user = X
password = X

[RABBITMQ]
HOST= X
PORT= X
USER= X
PASSWORD= X
INSTANCE_CONTROLLER_QUEUE= X
ACK_DEVICE_STATUS_QUEUE= X
ACK_DEVICE_DELETE_QUEUE= X


[HARDWARE_ACCELERATION]
PROCESSING_MODE=GPU | CPU
CUDA_VERSION= X #Not necessary if PROCESSING_MODE=CPU
```

Format of the image processor config file:

```ini
[DATABASE]
HOST= X
PORT= X
USER= X
PASSWORD= X

[MEDIA_SERVER]
DESTINATION_HOST = X
WRITE_USER = X
WRITE_PASSWORD = X

```

#### Media Server Authentication

This process is handled by the image processor.
The credentials are configured in the config file `./config/worker.ini` under the section.