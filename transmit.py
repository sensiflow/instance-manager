# code adapted for our application purposes   src: ./detected.py by YOLOv5 🚀 by Ultralytics, AGPL-3.0 license
"""
Changes:
 - Removed ability to save output and info to file

Run YOLOv5 detection inference on images, videos, directories, globs, YouTube, webcam, streams, etc.

Usage - sources:
    $ python detect.py --weights yolov5s.pt --source 0                               # webcam
                                                     img.jpg                         # image
                                                     vid.mp4                         # video
                                                     screen                          # screenshot
                                                     path/                           # directory
                                                     list.txt                        # list of images
                                                     list.streams                    # list of streams
                                                     'path/*.jpg'                    # glob
                                                     'https://youtu.be/Zgi9g1ksQHc'  # YouTube
                                                     'rtsp://example.com/media.mp4'  # RTSP, RTMP, HTTP stream

Usage - formats:
    $ python detect.py --weights yolov5s.pt                 # PyTorch
                                 yolov5s.torchscript        # TorchScript
                                 yolov5s.onnx               # ONNX Runtime or OpenCV DNN with --dnn
                                 yolov5s_openvino_model     # OpenVINO
                                 yolov5s.engine             # TensorRT
                                 yolov5s.mlmodel            # CoreML (macOS-only)
                                 yolov5s_saved_model        # TensorFlow SavedModel
                                 yolov5s.pb                 # TensorFlow GraphDef
                                 yolov5s.tflite             # TensorFlow Lite
                                 yolov5s_edgetpu.tflite     # TensorFlow Edge TPU
                                 yolov5s_paddle_model       # PaddlePaddle
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from time import sleep
import logging
import src.config as config
from src.config.app import get_worker_config
from src.image_processor import callbacks
from src.image_processor.metric.metric_dao import MetricDAOFactory
from src.image_processor.metric.metrics_service import DetectionMetricsService
from src.image_processor.processed_stream.processed_stream_dao import ProcessedStreamDAOFactory
from src.image_processor.processed_stream.processed_stream_service import ProcessedStreamService
from src.image_processor.streamer_rtsp import StreamerRTSP
from models.common import DetectMultiBackend
from utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadStreams
from utils.general import (LOGGER, Profile, check_file, check_img_size, check_requirements,
                           increment_path, non_max_suppression, print_args, scale_boxes, strip_optimizer, xyxy2xywh)
from utils.plots import Annotator, colors, save_one_box
from utils.torch_utils import select_device, smart_inference_mode

import argparse
import src.image_processor.logging_utils as logging_utils
import os
import sys
from pathlib import Path
from psycopg_pool import ConnectionPool
import torch

FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

FPS = 30


@smart_inference_mode()
def run_inference_model(
        weights=ROOT / 'yolov5s.pt',  # model path or triton URL
        source=ROOT / 'data/images',  # file/dir/URL/glob/screen/0(webcam)
        data=ROOT / 'data/coco128.yaml',  # dataset.yaml path
        imgsz=(480, 640),  # inference size (height, width)
        conf_thres=0.25,  # confidence threshold
        iou_thres=0.45,  # NMS IOU threshold
        max_det=1000,  # maximum detections per image
        device='0',  # cuda device, i.e. 0 or 0,1,2,3 or cpu
        classes=None,  # filter by class: --class 0, or --class 0 2 3
        agnostic_nms=False,  # class-agnostic NMS
        augment=False,  # augmented inference
        visualize=False,  # visualize features
        update=False,  # update all models
        project=ROOT / 'runs/detect',  # save results to project/name
        name='exp',  # save results to project/name
        exist_ok=False,  # existing project/name ok, do not increment
        line_thickness=3,  # bounding box thickness (pixels)
        hide_labels=False,  # hide labels
        hide_conf=False,  # hide confidences
        half=False,  # use FP16 half-precision inference
        dnn=False,  # use OpenCV DNN for ONNX inference
        vid_stride=1,  # video frame-rate stride,
        device_id=0,  # device id
        on_metric_detected=None,  # callback function to call when a detection is made
        on_stream_started=None,  # callback function to call when a stream is started
):
    source = str(source)
    destination = source + "/detected"
    streamer = None
    callback_executor = ThreadPoolExecutor(max_workers=1)

    is_file = Path(source).suffix[1:] in (IMG_FORMATS + VID_FORMATS)
    if is_file:
        logging_utils.logError(1, "File input is not supported")
        logging_utils.logShutdown()
        return
    is_url = source.lower().startswith(('rtsp://', 'rtmp://', 'http://', 'https://'))
    webcam = source.isnumeric() or source.endswith(
        '.streams') or (is_url and not is_file)

    if is_url and is_file:
        source = check_file(source)  # download

    # Directories
    save_dir = increment_path(Path(project) / name,
                              exist_ok=exist_ok)  # increment run
    save_dir.mkdir(parents=True, exist_ok=True)  # make dir

    # Load model
    device = select_device(device)
    model = DetectMultiBackend(
        weights, device=device, dnn=dnn, data=data, fp16=half)
    stride, names, pt = model.stride, model.names, model.pt
    imgsz = check_img_size(imgsz, s=stride)  # check image size

    logging_utils.logSuccess(1, "Loaded model")

    try:
        # Dataloader
        bs = 1  # batch_size
        if webcam:

            dataset = LoadStreams(source, img_size=imgsz,
                                  stride=stride, auto=pt, vid_stride=vid_stride)
            bs = len(dataset)
        else:
            dataset = LoadImages(source, img_size=imgsz,
                                 stride=stride, auto=pt, vid_stride=vid_stride)

        callback_executor.submit(on_stream_started, destination)

        logging_utils.logSuccess(2, "Got feed from the input")
    except Exception as e:
        logging_utils.logError(2, "Failed to get feed from the input")
        logging_utils.logShutdown()
        raise e

    # Run inference
    model.warmup(imgsz=(1 if pt or model.triton else bs, 3, *imgsz))  # warmup
    seen, _, dt = 0, [], (Profile(), Profile(), Profile())
    for path, im, im0s, vid_cap, s in dataset:
        with dt[0]:
            im = torch.from_numpy(im).to(model.device)
            im = im.half() if model.fp16 else im.float()  # uint8 to fp16/32
            im /= 255  # 0 - 255 to 0.0 - 1.0
            if len(im.shape) == 3:
                im = im[None]  # expand for batch dim

        with dt[1]:
            visualize = increment_path(
                save_dir / Path(path).stem, mkdir=True) if visualize else False
            pred = model(im, augment=augment, visualize=visualize)

        # NMS
        with dt[2]:
            pred = non_max_suppression(
                pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)

        # Second-stage classifier (optional)
        # pred = utils.general.apply_classifier(pred, classifier_model, im, im0s)

        # Process predictions
        for i, det in enumerate(pred):  # per image
            seen += 1
            if webcam:  # batch_size >= 1
                p, im0, frame = path[i], im0s[i].copy(), dataset.count
                s += f'{i}: '
            else:
                p, im0, frame = path, im0s.copy(), getattr(dataset, 'frame', 0)
            # Setup streamer
            if streamer is None:
                streamer = StreamerRTSP(
                    destination, im0.shape[1], im0.shape[0], FPS)
                logging_utils.logSuccess(3, "Streamer object created")
                streamer.start_stream()
                logging_utils.logSuccess(4, "Streamer object started")

            s += '%gx%g ' % im.shape[2:]  # print string
            annotator = Annotator(
                im0, line_width=line_thickness, example=str(names))

            detections_info = {}
            if len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_boxes(
                    im.shape[2:], det[:, :4], im0.shape).round()

                for c in det[:, 5].unique():
                    n_tensor = (det[:, 5] == c).sum()  # detections per class
                    class_name = names[int(c)]
                    n_detections = n_tensor.item()
                    detections_info[class_name] = n_detections
                # Write results
                for *xyxy, conf, cls in reversed(det):
                    # Detection bboxes
                    c = int(cls)  # integer class
                    label = None if hide_labels else (
                        names[c] if hide_conf else f'{names[c]} {conf:.2f}')
                    annotator.box_label(xyxy, label, color=colors(c, True))

                # Print time (inference-only)
                for class_name, n_detections in detections_info.items():
                    s += f"{n_detections} {class_name}{'s' * (n_detections > 1)}, "

            if on_metric_detected is not None:
                callback_executor.submit(
                    on_metric_detected, detections_info)

            # Stream results
            im0 = annotator.result()
            streamer.next_frame(im0)

        LOGGER.info(
            f"{s}{'' if len(det) else '(no detections), '}{dt[1].dt * 1E3:.1f}ms")

    t = tuple(x.t / seen * 1E3 for x in dt)  # speeds per image
    LOGGER.info(
        f'Speed: %.1fms pre-process, %.1fms inference, %.1fms NMS per image at shape {(1, 3, *imgsz)}' % t)

    if update:
        # update model (to fix SourceChangeWarning)
        strip_optimizer(weights[0])


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', nargs='+', type=str,
                        default=ROOT / 'yolov5s.pt', help='model path or triton URL')
    parser.add_argument('--source', type=str, default=ROOT /
                        'data/images', help='file/dir/URL/glob/screen/0(webcam)')
    parser.add_argument('--data', type=str, default=ROOT /
                        'data/coco128.yaml', help='(optional) dataset.yaml path')
    parser.add_argument('--imgsz', '--img', '--img-size', nargs='+',
                        type=int, default=[640], help='inference size h,w')
    parser.add_argument('--conf-thres', type=float,
                        default=0.5, help='confidence threshold')
    parser.add_argument('--iou-thres', type=float,
                        default=0.45, help='NMS IoU threshold')
    parser.add_argument('--max-det', type=int, default=1000,
                        help='maximum detections per image')
    parser.add_argument('--device', default='',
                        help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--classes', nargs='+', type=int,
                        help='filter by class: --classes 0, or --classes 0 2 3')
    parser.add_argument('--agnostic-nms', action='store_true',
                        help='class-agnostic NMS')
    parser.add_argument('--augment', action='store_true',
                        help='augmented inference')
    parser.add_argument('--visualize', action='store_true',
                        help='visualize features')
    parser.add_argument('--update', action='store_true',
                        help='update all models')
    parser.add_argument('--project', default=ROOT /
                        'runs/detect', help='save results to project/name')
    parser.add_argument('--name', default='exp',
                        help='save results to project/name')
    parser.add_argument('--exist-ok', action='store_true',
                        help='existing project/name ok, do not increment')
    parser.add_argument('--line-thickness', default=3,
                        type=int, help='bounding box thickness (pixels)')
    parser.add_argument('--hide-labels', default=False,
                        action='store_true', help='hide labels')
    parser.add_argument('--hide-conf', default=False,
                        action='store_true', help='hide confidences')
    parser.add_argument('--half', action='store_true',
                        help='use FP16 half-precision inference')
    parser.add_argument('--dnn', action='store_true',
                        help='use OpenCV DNN for ONNX inference')
    parser.add_argument('--vid-stride', type=int, default=1,
                        help='video frame-rate stride')
    parser.add_argument('--device-id', type=int, default=-1,
                        help='device\'s id where the metrics and processed stream are sent to', required=True)
    opt = parser.parse_args()
    opt.imgsz *= 2 if len(opt.imgsz) == 1 else 1  # expand
    print_args(vars(opt))
    return opt


async def main(opt):
    check_requirements(exclude=('tensorboard', 'thop'))

    device_id = opt.device_id
    if device_id == -1:
        print("Please provide a device id to send the metrics and processed stream to")
        exit(1)

    cfg_parser = config.parse_config(config.get_environment_type())

    worker_cfg = get_worker_config(cfg_parser)
    database_cfg = worker_cfg["database"]
    database_url = (
        f"postgres://{database_cfg['user']}:{database_cfg['password']}"
        f"@{database_cfg['host']}:{database_cfg['port']}"
    )

    logging.info("Connecting to %s", database_url)

    with ConnectionPool(database_url, min_size=5) as connection_manager:

        metrics_service = DetectionMetricsService(
            connection_manager,
            MetricDAOFactory(),
            device_id
        )

        processed_service = ProcessedStreamService(
            connection_manager,
            ProcessedStreamDAOFactory(),
            device_id
        )

        on_metric_detected = callbacks.get_on_metric_received_callback(
            metrics_service)
        on_detection_started = callbacks.get_on_stream_started_callback(
            processed_service)

        # Blocks the main thread, calling the callback functions in another
        run_inference_model(
            **vars(opt),
            on_metric_detected=on_metric_detected,
            on_stream_started=on_detection_started
        )

    logging.info("Finished closing connection pool.")

if __name__ == '__main__':
    opt = parse_opt()
    asyncio.run(main(opt))
