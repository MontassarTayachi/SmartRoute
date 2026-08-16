"""
Production WSGI entrypoint (Render, or any gunicorn/eventlet host).

eventlet.monkey_patch() must run before anything else imports socket/ssl-using
libraries (pymongo, requests, ...) - importing app.main here, before patching,
would patch too late and lead to blocking I/O inside the eventlet workers.

Start command: gunicorn --worker-class eventlet -w 1 wsgi:app
"""
import eventlet
eventlet.monkey_patch()

from app.main import create_app_with_scheduler  # noqa: E402

app = create_app_with_scheduler()
