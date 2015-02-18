import multiprocessing

#gunicorn -c gunicorn_config.py main

proc_name = "clam"
bind = "0.0.0.0:8000"
workers = multiprocessing.cpu_count() * 2 + 1

# File upload timeouts
timeout = 60 * 60 * 24
limit_request_field_size = 80 * 1024

preload = True