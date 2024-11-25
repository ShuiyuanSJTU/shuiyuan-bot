import hmac
import hashlib
import ipaddress
from flask import request, abort, Request


def verify_discourse_webhook_request(request: Request, secret: str) -> bool:
    if not secret:
        return True
    sig = request.headers.get('X-Discourse-Event-Signature', '')[7:]
    if sig:
        payload = request.data
        computed_sig = hmac.new(secret.encode(), payload,
                                hashlib.sha256).hexdigest()
        if computed_sig == sig:
            return True
        else:
            return False


def verify_ip_address(request: Request, whitelist_ips: list[str], reverse_proxy_ips: list[str]) -> bool:
    if not whitelist_ips:
        return True
    return in_whitelist(extract_real_ip(request, reverse_proxy_ips), whitelist_ips)


def in_whitelist(ip, whitelist_ips) -> bool:
    if ip in whitelist_ips:
        return True
    for net in whitelist_ips:
        if ipaddress.ip_address(ip) in ipaddress.ip_network(net):
            return True
    return False


def extract_real_ip(request: Request, reverse_proxy_ips: list[str]) -> str:
    x_forwarded_for = request.headers.get('X-Forwarded-For')

    if x_forwarded_for and request.remote_addr in reverse_proxy_ips:
        ip_addresses = x_forwarded_for.split(',')

        for ip in ip_addresses:
            ip = ip.strip()
            if ip not in reverse_proxy_ips:
                return ip

    return request.remote_addr


def verify_discourse_instance(request: Request, instance_name: str) -> bool:
    if not instance_name:
        return True
    return request.headers.get('X-Discourse-Instance') == instance_name
