
import eventlet
import logging
from flask import Flask
from flask import request, abort
from eventlet import wsgi
from logging.handlers import RotatingFileHandler

# Set up logging
logging.getLogger('werkzeug').setLevel(logging.WARNING)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler = RotatingFileHandler('app.warning.log', maxBytes=1024 * 1024, backupCount=2)
file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.WARNING)

root_logger = logging.getLogger()
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# Set up the server
from backend.bot import Config, BotManager
from security import verify_discourse_webhook_request, verify_ip_address, verify_discourse_instance

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
    logging.info(f"Starting server on {Config.server.bind_address}:{Config.server.bind_port}")
    wsgi.server(eventlet.listen(
        (Config.server.bind_address, Config.server.bind_port)), app, log_output=False)
