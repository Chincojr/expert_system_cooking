"""Single-process deployment for the small, editable recipe knowledge base."""
import os

bind = "0.0.0.0:" + os.environ.get("PORT", "8000")
workers = 1
threads = 1
timeout = 60
accesslog = "-"
errorlog = "-"
