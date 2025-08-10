# DD Network Webhook Templates - Updated

## 配置文件格式说明

新的配置文件采用更清晰的结构：
- `ips`: 存储各类IP地址（IPv4, IPv6_ddasus, IPv6_dd）
- `stun_ports`: 存储各服务的STUN端口
- `services`: 存储服务配置，合并IPv4/IPv6的原始端口
- `domains`: 存储各网络的域名
- `auth`: 认证信息

## Webhook API 端点

> **所有 Webhook 接口现已强制要求 HTTP Basic Auth 认证，用户名和密码与 dashboard 相同。**

### 1. 更新IP地址 (POST /dd/webhook/update_ip/<ip_type>)

支持的ip_type: `ipv4`, `ipv6_ddasus`, `ipv6_dd`

```json
{
    "ip": "新的IP地址"
}
```

**示例:**
```bash
# 更新IPv4地址
curl -X POST http://your-server/dd/webhook/update_ip/ipv4 \
  -u "barry:G8p9MET3Gg" \
  -H "Content-Type: application/json" \
  -d '{"ip": "223.102.174.43"}'

# 更新IPv6 ddasus地址
curl -X POST http://your-server/dd/webhook/update_ip/ipv6_ddasus \
  -u "barry:G8p9MET3Gg" \
  -H "Content-Type: application/json" \
  -d '{"ip": "2409:8a15:5860:ce60::1"}'

# 更新IPv6 dd地址
curl -X POST http://your-server/dd/webhook/update_ip/ipv6_dd \
  -u "barry:G8p9MET3Gg" \
  -H "Content-Type: application/json" \
  -d '{"ip": "2409:8a15:5860:ce60:67c:16ff:fe85:24c2"}'
```

### 2. 更新单个STUN端口 (POST /dd/webhook/update_stun_port)

支持的service_name: `ddasus_web`, `dd_rdp`, `dorm_rdp`, `dorm_ssh`, `ddasus_frps`

```json
{
    "service_name": "服务名",
    "port": 端口号
}
```

**示例:**
```bash
# 使用header方式传递Basic Auth
curl -X POST http://your-server/dd/webhook/update_stun_port \
  -H "Authorization: Basic YmFycnk6RzhwOU1FVDNHZw==" \
  -H "Content-Type: application/json" \
  -d '{"service_name": "ddasus_web", "port": 12203}'
```

## 访问方式

### Dashboard (需要认证)
- `/dd/` - 主仪表板，显示所有服务
- `/dd/status` - 配置状态API

### 服务重定向 (无需认证)
- `/dd/<service_name>` - IPv4服务重定向
- `/dd6/<service_name>` - IPv6服务重定向

## 重定向行为

### IPv4重定向
- Web服务: 直接重定向到 `http(s)://IP:原始端口`
- 其他服务: 返回文本 `IP:原始端口`

### IPv6重定向
- Web服务: 重定向到 `http(s)://域名:原始端口`
- 其他服务: 返回文本 `域名:原始端口`

## Dashboard显示

Dashboard会同时显示：
1. **直接IP访问**: 使用真实IP和原始端口
2. **域名访问**: 使用域名和STUN端口（仅web服务且有subdomain）
3. **STUN端口信息**: 显示当前STUN端口

## Python客户端示例

```python
import requests

class DDNetworkUpdater:
    def __init__(self, base_url, username, password):
        self.base_url = base_url.rstrip('/')
        self.auth = (username, password)
    
    def update_ip(self, ip_type, ip_address):
        """更新IP地址"""
        url = f"{self.base_url}/dd/webhook/update_ip/{ip_type}"
        response = requests.post(url, json={"ip": ip_address}, auth=self.auth)
        return response.json()
    
    def update_stun_port(self, service_name, port):
        """更新单个STUN端口"""
        url = f"{self.base_url}/dd/webhook/update_stun_port/{service_name}"
        response = requests.post(url, json={"port": port}, auth=self.auth)
        return response.json()
    
    def update_all_stun_ports(self, stun_ports):
        """批量更新STUN端口"""
        url = f"{self.base_url}/dd/webhook/update_all_stun_ports"
        response = requests.post(url, json={"stun_ports": stun_ports}, auth=self.auth)
        return response.json()

# 使用示例
updater = DDNetworkUpdater("http://your-server", "barry", "G8p9MET3Gg")

# 更新IPv4地址
updater.update_ip("ipv4", "223.102.174.43")

# 更新STUN端口
updater.update_stun_port("ddasus_web", 12203)

# 批量更新
updater.update_all_stun_ports({
    "ddasus_web": 12203,
    "dd_rdp": 12194
})
```

## 注意事项

1. **认证**: dashboard页面和所有webhook接口都需要HTTP基本认证（Basic Auth），用户名和密码见config.json的auth字段。
2. **端口分离**: STUN端口仅用于dashboard显示域名访问方式
3. **原始端口**: IPv4/IPv6重定向使用原始端口，确保服务可达
4. **域名访问**: IPv6使用域名访问避免DNS TTL问题
5. **错误处理**: 所有webhook返回JSON格式的成功/错误消息
