"""Configuration values for the Smart Transit Security detection module."""

CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 640
CONFIDENCE_THRESHOLD = 0.45
NMS_IOU_THRESHOLD = 0.5
YOLO_MODEL_NAME = "yolo11n.pt"
TARGET_CLASSES = ["person", "backpack", "handbag", "suitcase"]
DWELL_THRESHOLD_SECONDS = 10.0
UNATTENDED_THRESHOLD_SECONDS = 15.0
API_ENDPOINT = "http://localhost:8002/events"
POST_TIMEOUT_SECONDS = 2.0
ZONES_FILE = "zones.json"
DEVICE = "cuda"
HALF_PRECISION = True
LOG_LEVEL = "INFO"
FPS_LOG_INTERVAL = 100
TARGET_FRAME_TIME_SECONDS = 1.0 / 30.0
WINDOW_NAME = "Smart Transit Security"
