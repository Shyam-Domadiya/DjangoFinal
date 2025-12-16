# Gunicorn configuration for production deployment on Render
import os
import multiprocessing

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', 8000)}"
backlog = 2048

# Worker processes
workers = max(2, multiprocessing.cpu_count())
worker_class = 'sync'
worker_connections = 1000
timeout = 60
keepalive = 2

# Logging
accesslog = '-'  # Log to stdout
errorlog = '-'   # Log to stderr
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'demodev'

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (handled by Render's reverse proxy, not needed here)
keyfile = None
certfile = None

# Application
raw_env = []

# Debugging
reload = False
reload_extra_files = []

# Server hooks
def on_starting(server):
    print("[GUNICORN] Starting server...")

def when_ready(server):
    print(f"[GUNICORN] Server is ready. Spawning workers on {bind}")

def on_exit(server):
    print("[GUNICORN] Server shutting down...")
