"""Configuration values for the Smart Transit Security analytics module."""

LOITERING_THRESHOLD_SECONDS = 30.0
CROWD_SURGE_THRESHOLD = 3
UNATTENDED_THRESHOLD_SECONDS = 15.0
THEFT_CONFIDENCE_THRESHOLD = 0.55
DEDUP_WINDOW_SECONDS = 10.0
CLIP_DURATION_SECONDS = 10
CLIPS_DIR = "clips"
P3_EVENTS_ENDPOINT = "http://localhost:8001/api/v1/events"
P3_ALERTS_ENDPOINT = "http://localhost:8001/api/v1/alerts"
P3_ANALYTICS_RESULTS_ENDPOINT = "http://localhost:8001/api/v1/analytics-results"
POST_TIMEOUT_SECONDS = 2.0
ANALYTICS_HOST = "0.0.0.0"
ANALYTICS_PORT = 8002
DEVICE = "cuda"
FIREBASE_CREDENTIALS_FILE = "firebase_config.json"
FIREBASE_HIGH_SEVERITY_ONLY = True
FRAME_WIDTH = 640
FRAME_HEIGHT = 640
TARGET_FPS = 30
THEFT_VELOCITY_THRESHOLD = 80.0
THEFT_PROXIMITY_THRESHOLD = 0.12

# Zone-specific crowd density thresholds
# Maps zone_id to person count threshold for that zone
ZONE_CROWD_THRESHOLDS = {
    "zone_001": 4,  # entry turnstiles - allow 4 people before surge
    "zone_002": 3,  # platform waiting zone - allow 3 people before surge
    "zone_003": 2,  # staff only - very restrictive, allow only 2
}

# Owner departure grace period before starting unattended timer
OWNER_DEPARTURE_GRACE_SECONDS = 2.0

# Distance threshold for proximity-based object tracking
OBJECT_PROXIMITY_THRESHOLD = 150.0

# Maximum distance for object movement before resetting timer
OBJECT_STATIONARITY_THRESHOLD = 20.0
