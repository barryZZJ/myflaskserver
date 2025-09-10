import json
import dns.resolver
from functools import wraps
from flask import Blueprint, Response, request, redirect, render_template
from loguru import logger
from wecom_responder.utils.consts import CONFIG_FILE_DDREDIRECT

# Create a Blueprint object for the main section
bp_ddredirect = Blueprint('ddredirect', __name__, url_prefix='/dd', template_folder='templates')

# 配置文件路径
#! 因为这里的内容会经常变化，因此不存入main config file
CONFIG_FILE = CONFIG_FILE_DDREDIRECT

def load_config():
    """加载配置文件"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"配置文件不存在: {CONFIG_FILE}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"配置文件格式错误: {e}")
        return None

def save_config(config):
    """保存配置文件"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"保存配置文件失败: {e}")
        return False

def require_auth(f):
    """基本认证装饰器 - 仅用于dashboard"""
    @wraps(f)
    def decorated(*args, **kwargs):
        config = load_config()
        if not config:
            return "Load config file failed", 500

        auth = request.authorization
        if not auth or not (auth.username == config['auth']['username'] and
                           auth.password == config['auth']['password']):
            return Response(
                'Need authentication', 401,
                {'WWW-Authenticate': 'Basic realm="DD Network Access"'}
            )
        return f(*args, **kwargs)
    return decorated

def resolve_txt_record(domain):
    """解析域名的TXT记录"""
    try:
        result = dns.resolver.resolve(domain, 'TXT')
        txt_records = [str(record).strip('"') for record in result]
        return txt_records
    except Exception as e:
        logger.warning(f"解析TXT记录失败: {domain} - {e}")
        return []

def get_ip_from_txt(domain):
    """从TXT记录中提取IP地址"""
    txt_records = resolve_txt_record(domain)
    for record in txt_records:
        # 假设TXT记录格式为 "ip=xxx.xxx.xxx.xxx" 或直接是IP地址
        if record.count('.') == 3 or ':' in record:  # 简单IP格式检查
            return record
    return None

def resolve_dns_ips(config):
    """解析DNS TXT记录获取IP地址"""
    dns_ips = {}
    for key, domain in config['TXT'].items():
        resolved = get_ip_from_txt(domain)
        if resolved:
            dns_ips[f"{key}_txt"] = resolved

    return dns_ips

@bp_ddredirect.route('/')
@require_auth
def index():
    """显示所有重定向信息的HTML页面"""
    config = load_config()
    if not config:
        return "配置文件错误", 500

    # 解析DNS TXT记录
    dns_ips = resolve_dns_ips(config)

    from datetime import datetime
    return render_template('dashboard.html',
                          config=config,
                          dns_ips=dns_ips,
                          timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@bp_ddredirect.route('/<service_name>/<path:req_path>')
@bp_ddredirect.route('/<service_name>')
def ipv4_redirect(service_name, req_path=''):
    """IPv4服务重定向 - 不需要认证"""
    config = load_config()
    if not config:
        return "配置文件错误", 500

    service = config['services'].get(service_name)
    if not service:
        return f"IPv4服务 {service_name} 不存在", 404

    ip = config['ips']['ipv4']

    # 动态获取端口：web服务使用ddasus_web端口，service服务使用同名端口
    if service['type'] == 'web':
        port = config['stun_ports'].get('ddasus_web')
    else:  # service类型
        port = config['stun_ports'].get(service_name)

    if not port:
        return f"IPv4服务 {service_name} 端口配置不存在", 404

    # 确定使用哪个IPv6主机的IP和域名
    if 'ipv4_domain' in service:
        host_key = f'ipv4_{service["ipv4_domain"]}'
        domain = config['domains'][host_key]
    else:
        domain = config['domains']['ipv4']

    if service['type'] == 'web':
        path = service.get('path', '')
        req_path = ('/' + req_path) if req_path else ''
        url = f"{service['ipv4_scheme']}://{service['subdomain']}.{domain}:{port}{path}{req_path}"
        logger.info(f"重定向到 IPv4 web 服务: {service_name} -> {url}")
        return redirect(url)
    else:
        address = f"{ip}:{port}"
        url = f"{domain}:{port}"
        resp = f"{address}\n{url}"
        logger.info(f"返回 IPv4 服务地址: {service_name} -> {address}\n{service_name} -> {url}")
        return Response(resp, mimetype='text/plain')

@bp_ddredirect.route('/6/')
@require_auth
def ipv6_index():
    """显示IPv6重定向信息的HTML页面"""
    return redirect('/dd/')  # 重定向到主dashboard

@bp_ddredirect.route('/6/<service_name>')
def ipv6_redirect(service_name):
    """IPv6服务重定向 - 不需要认证，使用TXT记录解析的IP地址"""
    config = load_config()
    if not config:
        return "配置文件错误", 500

    service = config['services'].get(service_name)
    if not service or not service.get('ipv6_host') or not service.get('original_port'):
        return f"IPv6服务 {service_name} 不存在或未配置", 404

    # 确定使用哪个IPv6主机的IP和域名
    host_key = f'ipv6_{service["ipv6_host"]}'

    if 'nspshare' in service["ipv6_host"]:
        configured_ip = config['ips']['ipv6_ddasus']
    else:
        if host_key not in config['ips']:
            return f"IPv6服务 {service_name} 主机配置错误", 404

        configured_ip = config['ips'][host_key]
    domain = config['domains'][host_key]
    port = service['original_port']

    # 从TXT记录获取解析的IP
    dns_ips = resolve_dns_ips(config)
    txt_ip_key = f'{host_key}_txt'
    txt_ip = dns_ips.get(txt_ip_key)

    # 检查是否使用域名访问
    use_domain = False

    # 如果TXT记录存在且与配置IP一致，则使用域名访问
    if txt_ip and txt_ip == configured_ip:
        use_domain = True
        logger.warning(f"TXT记录IP {txt_ip} 与配置实时IP {configured_ip} 一致，使用域名访问")
    elif txt_ip:
        logger.info(f"TXT记录IP {txt_ip} 与配置实时IP {configured_ip} 不一致，使用IP访问")
    else:
        logger.info(f"无TXT记录，使用配置IP {configured_ip} 访问")

    if service['type'] == 'web':
        path = service.get('path', '')
        if use_domain:
            url = f"{service['ipv6_scheme']}://{domain}:{port}{path}"
        else:
            url = f"{service['ipv6_scheme']}://[{configured_ip}]:{port}{path}"

        logger.info(f"重定向到 IPv6 web 服务: {service_name} -> {url}")
        return redirect(url)
    else:
        if use_domain:
            address = f"{domain}:{port}"
            fallback_address = f"[{configured_ip}]:{port}"
        else:
            address = f"[{configured_ip}]:{port}"
            fallback_address = f"{domain}:{port}"

        resp = f"{address}\n{fallback_address}"
        logger.info(f"返回 IPv6 服务地址: {service_name} -> {address} (备用: {fallback_address})")
        return Response(resp, mimetype='text/plain')

# Webhook routes for updating configuration
@bp_ddredirect.route('/webhook/update_ip/<ip_type>', methods=['POST'])
@require_auth
def webhook_update_ip(ip_type):
    """更新IP地址的webhook"""
    try:
        data = request.get_json()
        if not data or 'ip' not in data:
            return {"error": f"Invalid {ip_type} IP data."}, 400

        config = load_config()
        if not config:
            return {"error": "Failed to load current config."}, 500

        if ip_type not in config['ips']:
            return {"error": f"Unsupported IP type: {ip_type}"}, 400

        config['ips'][ip_type] = data['ip']

        if save_config(config):
            logger.info(f"{ip_type} IP updated via webhook: {data['ip']}")
            return {"message": f"{ip_type} IP updated successfully."}, 200
        else:
            return {"error": f"Failed to save {ip_type} IP."}, 500

    except Exception as e:
        logger.error(f"Webhook更新{ip_type} IP失败: {e}")
        return {"error": str(e)}, 500

@bp_ddredirect.route('/webhook/update_stun_port', methods=['POST'])
@require_auth
def webhook_update_stun_port():
    """Update STUN port and IP via webhook"""
    try:
        data = request.get_json()
        if not data or 'port' not in data or 'service_name' not in data or 'ip' not in data:
            return {"error": "Invalid STUN port data. Required: service_name, port, ip."}, 400

        config = load_config()
        if not config:
            return {"error": "Failed to load current config."}, 500

        service_name = data['service_name']
        config['stun_ports'][service_name] = data['port']
        # Also update IP for the corresponding IPv4
        config['ips']['ipv4'] = data['ip']

        if save_config(config):
            logger.info(f"{service_name} STUN port updated via webhook: {data['port']}, IPv4 updated: {data['ip']}")
            return {"message": f"STUN port for {service_name} and IPv4 updated successfully."}, 200
        else:
            return {"error": f"Failed to save STUN port for {service_name}."}, 500

    except Exception as e:
        logger.error(f"Webhook更新 STUN端口失败: {e}")
        return {"error": str(e)}, 500

