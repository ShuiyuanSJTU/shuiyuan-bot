from flask import Flask
from flask import request, abort
from backend.bot import BotManager
from backend.bot_config import config as CONFIG
from security import verify_discourse_webhook_request, verify_ip_address, verify_discourse_instance

import eventlet
import logging
from eventlet import wsgi
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

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

@app.before_request
def verify_request():
    if request.method == 'POST':
        if not verify_discourse_instance(request, CONFIG.server.discourse_instance_name):
            abort(403)
        if not verify_ip_address(request, CONFIG.server.whitelist_ips, CONFIG.server.reverse_proxy_ips):
            abort(403)
        if not verify_discourse_webhook_request(request, CONFIG.server.webhook_secret):
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
    wsgi.server(eventlet.listen(
        (CONFIG.server.bind_address, CONFIG.server.bind_port)), app, log_output=False)
