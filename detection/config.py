"""Configuration values for the Smart Transit Security detection module."""

CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 360
CONFIDENCE_THRESHOLD = 0.45
NMS_IOU_THRESHOLD = 0.5
YOLO_MODEL_NAME = "yolo11n.pt"
TARGET_CLASSES = ["person", "backpack", "handbag", "suitcase"]
DWELL_THRESHOLD_SECONDS = 10.0
UNATTENDED_THRESHOLD_SECONDS = 15.0
API_ENDPOINT = "http://localhost:8000/events"
POST_TIMEOUT_SECONDS = 2.0
ZONES_FILE = "zones.json"
DEVICE = "cuda"
HALF_PRECISION = True
INFERENCE_IMAGE_SIZE = 416
GLOBAL_ZONE_ID = "all_regions"
TRACK_MAX_AGE = 8
TRACK_N_INIT = 2
LOG_LEVEL = "INFO"
FPS_LOG_INTERVAL = 100
WINDOW_NAME = "Smart Transit Security"
