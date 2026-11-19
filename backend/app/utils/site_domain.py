"""站点域名（项目访问地址）配置的读取、校验与对外表示。

站点设置里保存两项：

* ``domain_mode``：``auto`` 跟随访问地址；``manual`` 固定使用 ``domain``。
* ``domain``：手动模式下保存的 ``scheme://host[:port]``。

历史部署没有这两行配置时视为「沿用原有部署配置」（legacy），由前端继续使用
构建时写入的接口前缀，保证升级后行为不变。新建站点会在初始化时写入
``domain_mode=auto``，从而表现为「用户用什么地址访问，就请求哪个地址」。
"""

import re
from urllib.parse import urlsplit

from app import db
from app.models import Setting

DOMAIN_MODE_ALIAS = 'domain_mode'
DOMAIN_ALIAS = 'domain'
SITE_SETTING_GROUP = 'site_setting'

DOMAIN_MODE_AUTO = 'auto'
DOMAIN_MODE_MANUAL = 'manual'
# legacy：沿用升级前构建时写入的接口地址（前台的 VITE_API_URL / 管理端的
# window.ipConfig）。升级站点没有保存过域名配置时默认落到这个模式，保证行为不变。
DOMAIN_MODE_LEGACY = 'legacy'
DOMAIN_MODES = (DOMAIN_MODE_AUTO, DOMAIN_MODE_MANUAL, DOMAIN_MODE_LEGACY)

MAX_DOMAIN_LENGTH = 255

# 主机名允许字母、数字、点、连字符、下划线和国际化字符；IPv6 字面量单独放行。
_HOST_RE = re.compile(r'^[A-Za-z0-9._\-\u0080-\uffff]+$')
_IPV6_RE = re.compile(r'^[0-9A-Fa-f:.]+$')


class DomainValidationError(ValueError):
    """用户填写的项目域名不合法。"""


def _clean(value):
    return str(value or '').strip()


def get_site_domain_config():
    """读取站点域名配置。

    返回 ``configured`` 表示数据库中是否存在显式的 ``domain_mode`` 行：
    False 说明是升级上来的历史站点，前端应沿用原有部署配置。
    """
    rows = Setting.query.filter(
        Setting.alias.in_((DOMAIN_MODE_ALIAS, DOMAIN_ALIAS))
    ).all()
    values = {row.alias: _clean(row.value) for row in rows}
    configured = DOMAIN_MODE_ALIAS in values
    if configured:
        mode = values.get(DOMAIN_MODE_ALIAS, DOMAIN_MODE_LEGACY).lower()
        if mode not in DOMAIN_MODES:
            mode = DOMAIN_MODE_LEGACY
    else:
        mode = DOMAIN_MODE_LEGACY
    domain = values.get(DOMAIN_ALIAS, '')
    if mode == DOMAIN_MODE_MANUAL and domain:
        try:
            domain = normalize_project_domain(domain)
        except DomainValidationError:
            # 历史脏数据不能让站点配置接口整体失败；按未配置处理。
            domain = ''
    return {
        'domain_mode': mode,
        'domain': domain,
        'configured': configured,
    }


def normalize_project_domain(raw_value):
    """把用户输入规范化为 ``scheme://host[:port]``。

    允许省略协议（默认 http）。只接受站点根地址：不允许路径、查询串、锚点、
    用户名密码；端口必须是 1-65535 的整数。
    """
    value = _clean(raw_value)
    if not value:
        raise DomainValidationError('请填写项目域名或 IP 地址')
    if len(value) > MAX_DOMAIN_LENGTH:
        raise DomainValidationError('项目域名过长')
    if any(character.isspace() for character in value) or any(
        ord(character) < 32 or ord(character) == 127 for character in value
    ):
        raise DomainValidationError('项目域名不能包含空格或控制字符')
    if any(character in value for character in ('\\', '"', "'", '<', '>', '`')):
        raise DomainValidationError('项目域名包含非法字符')

    candidate = value if '://' in value else f'http://{value}'
    parsed = urlsplit(candidate)
    scheme = parsed.scheme.lower()
    if scheme not in ('http', 'https'):
        raise DomainValidationError('仅支持 http:// 或 https:// 地址')
    if parsed.username or parsed.password:
        raise DomainValidationError('项目域名不能包含用户名或密码')
    if parsed.query or parsed.fragment:
        raise DomainValidationError('项目域名不能包含查询参数或锚点')
    if parsed.path not in ('', '/'):
        raise DomainValidationError('项目域名只能填写站点根地址，不能带路径')

    hostname = parsed.hostname
    if not hostname:
        raise DomainValidationError('项目域名缺少主机名或 IP')
    try:
        port = parsed.port
    except ValueError as exc:
        raise DomainValidationError('端口号无效，应为 1-65535') from exc
    if port is not None and not 1 <= port <= 65535:
        raise DomainValidationError('端口号无效，应为 1-65535')

    if ':' in hostname:
        if not _IPV6_RE.fullmatch(hostname):
            raise DomainValidationError('IPv6 地址格式无效')
        host_part = f'[{hostname.lower()}]'
    else:
        if not _HOST_RE.fullmatch(hostname):
            raise DomainValidationError('主机名包含非法字符')
        host_part = hostname.lower()

    netloc = host_part if port is None else f'{host_part}:{port}'
    return f'{scheme}://{netloc}'


def site_config_payload():
    """返回前端/管理端可直接消费的站点域名配置。"""
    config = get_site_domain_config()
    legacy = config['domain_mode'] == DOMAIN_MODE_LEGACY
    project_url = None
    api_prefix = None
    if config['domain_mode'] == DOMAIN_MODE_MANUAL and config['domain']:
        project_url = config['domain']
        api_prefix = f'{project_url}/api'
    return {
        'domain_mode': config['domain_mode'],
        'domain': config['domain'],
        'configured': config['configured'],
        'legacy': legacy,
        'project_url': project_url,
        'api_prefix': api_prefix,
    }


def save_site_domain_config(domain_mode=None, domain=None):
    """按需写入站点域名配置；只写传入的字段，未传入的保持原值。"""
    if domain_mode is not None:
        if domain_mode not in DOMAIN_MODES:
            raise DomainValidationError('域名模式无效')
        _upsert(DOMAIN_MODE_ALIAS, domain_mode)
    if domain is not None:
        _upsert(DOMAIN_ALIAS, domain)


def _upsert(alias, value):
    setting = Setting.query.filter_by(alias=alias).first()
    if setting is None:
        setting = Setting(alias=alias, group=SITE_SETTING_GROUP)
    setting.value = value
    setting.serialized = False
    setting.group = SITE_SETTING_GROUP
    db.session.add(setting)
