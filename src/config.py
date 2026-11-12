
from pathlib import Path

# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Data directories
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
QUARANTINE_DIR = BASE_DIR / "data" / "quarantine"
REPORTS_DIR = BASE_DIR / "data" / "reports"

# Generator configuration
RANDOM_SEED = 42
DEFAULT_RECORD_COUNT = 1_000

# Data lake configuration
PARTITION_COLUMN = "event_date"
TARGET_FILE_SIZE_MB = 128

# Allowed business values
VALID_EVENT_TYPES = [
    "order_placed",
    "payment_completed",
    "order_shipped",
    "order_delivered",
    "order_cancelled",
]

VALID_STATUSES = [
    "pending",
    "completed",
    "shipped",
    "delivered",
    "cancelled",
]
