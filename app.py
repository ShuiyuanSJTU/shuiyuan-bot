
import os
import logging
import signal
import sys
from flask import Flask
from flask import request, abort
from logging.handlers import RotatingFileHandler
from apscheduler.schedulers.background import BackgroundScheduler
from backend.bot import Config, BotManager
from security import verify_discourse_webhook_request, verify_ip_address, verify_discourse_instance

# Set up logging
logging.getLogger('werkzeug').setLevel(logging.WARNING)

os.makedirs('logs', exist_ok=True)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler = RotatingFileHandler('logs/app.warning.log', maxBytes=1024 * 1024, backupCount=2)
file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

root_logger = logging.getLogger()
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Set up the server
scheduler = BackgroundScheduler()
BotManager.register_jobs_to_scheduler(scheduler)
scheduler.start()

# Graceful shutdown: stop scheduler on SIGTERM/SIGINT to avoid long exit delays
def _shutdown(signum, frame):
    logging.info(f"Received signal {signum}, shutting down scheduler and exiting")
    try:
        scheduler.shutdown(wait=False)
    except Exception:
        logging.exception("Error while shutting down scheduler")
    sys.exit(0)
signal.signal(signal.SIGTERM, _shutdown)
signal.signal(signal.SIGINT, _shutdown)

app = Flask(__name__)

@app.before_request
def verify_request():
    if request.method == 'POST':
        if not verify_discourse_instance(request, Config.server.discourse_instance_name):
            abort(403)
        if not verify_ip_address(request, Config.server.whitelist_ips, Config.server.reverse_proxy_ips):
            abort(403)
        if not verify_discourse_webhook_request(request, Config.server.webhook_secret):
            abort(403)

@app.route("/",)
def root():
    return "OK"

@app.route("/", methods=['POST'])
def endpoint():
    data = request.get_json()
    event = request.headers.get('X-Discourse-Event')
    result = BotManager.trigger_event(event, data)
    if len(result) > 0:
        return "\n\n".join(map(str, result))
    else:
        return "ok"

if __name__ == "__main__":
    logging.info(f"Starting development server on {Config.server.bind_address}:{Config.server.bind_port}")
    # For development / local runs we use Flask's builtin server. In production,
    # prefer running with Gunicorn (see Dockerfile) to handle multiple workers.
    app.run(host=Config.server.bind_address, port=Config.server.bind_port)
