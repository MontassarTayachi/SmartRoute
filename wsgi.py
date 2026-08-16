"""
Production WSGI entrypoint (Render, or any gunicorn/gevent host).

gevent.monkey.patch_all() must run before anything else imports socket/ssl-using
libraries (pymongo, requests, ...) - importing app.main here, before patching,
would patch too late and lead to blocking I/O inside the gevent workers.

Start command: gunicorn --worker-class gunicorn.workers.ggevent.GeventWorker -w 1 wsgi:app
(the fully-qualified class path avoids entry-point resolution issues across
gunicorn versions — gunicorn 26 dropped the "eventlet" worker entirely; "gevent"
is still supported but the short alias has proven unreliable to resolve here)
"""
from gevent import monkey
monkey.patch_all()

from app.main import create_app_with_scheduler  # noqa: E402

app = create_app_with_scheduler()
