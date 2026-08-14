import re
import ipaddress
import socket
from urllib.parse import urljoin, urlparse
import uuid
from pathlib import Path


_INVALID_FILENAME = re.compile(r'[<>:"|?*\x00-\x1f\x7f]')


def safe_display_filename(filename: str) -> str:
    """Validate a user supplied filename without discarding Unicode names."""
    if not filename or not isinstance(filename, str):
        raise ValueError('文件名无效')
    normalized = filename.replace('\\', '/')
    if normalized != Path(normalized).name or normalized in {'.', '..'}:
        raise ValueError('文件名不得包含目录路径')
    if _INVALID_FILENAME.search(normalized):
        raise ValueError('文件名包含非法字符')
    if len(normalized) > 255:
        raise ValueError('文件名过长')
    return normalized


def stored_filename(filename: str) -> tuple[str, str]:
    """Return (display name, collision-resistant disk name)."""
    display = safe_display_filename(filename)
    suffix = Path(display).suffix.lower()
    stem = Path(display).stem[:180] or 'upload'
    return display, f'{uuid.uuid4().hex}_{stem}{suffix}'


def safe_storage_path(root: str | Path, *parts: str) -> Path:
    """Join storage components and reject traversal outside the storage root."""
    root_path = Path(root).resolve()
    candidate = root_path.joinpath(*parts).resolve()
    if not candidate.is_relative_to(root_path):
        raise ValueError('非法存储路径')
    return candidate


def validate_public_url(url: str) -> str:
    """Validate a URL before a server-side request, including DNS resolution."""
    parsed = urlparse(url)
    if parsed.scheme not in {'http', 'https'} or not parsed.hostname:
        raise ValueError('仅支持 HTTP/HTTPS 文件地址')
    try:
        addresses = {
            item[4][0]
            for item in socket.getaddrinfo(parsed.hostname, parsed.port or 443)
        }
    except socket.gaierror as exc:
        raise ValueError('文件地址无法解析') from exc
    for address in addresses:
        ip = ipaddress.ip_address(address)
        if (ip.is_private or ip.is_loopback or ip.is_link_local or
                ip.is_multicast or ip.is_reserved or ip.is_unspecified):
            raise ValueError('不允许访问内网文件地址')
    return url


def download_public_url(url: str, max_bytes: int) -> tuple[bytes, str]:
    """Download a bounded response while validating every redirect target."""
    import requests

    current_url = validate_public_url(url)
    for _ in range(5):
        response = requests.get(
            current_url,
            timeout=30,
            stream=True,
            allow_redirects=False,
        )
        if 300 <= response.status_code < 400:
            location = response.headers.get('Location')
            response.close()
            if not location:
                raise ValueError('远程文件重定向地址无效')
            current_url = validate_public_url(urljoin(current_url, location))
            continue
        response.raise_for_status()
        content_length = response.headers.get('Content-Length')
        if content_length and int(content_length) > max_bytes:
            response.close()
            raise ValueError('远程文件超过大小限制')
        chunks = []
        total = 0
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            total += len(chunk)
            if total > max_bytes:
                response.close()
                raise ValueError('远程文件超过大小限制')
            chunks.append(chunk)
        response.close()
        name = Path(urlparse(current_url).path).name
        return b''.join(chunks), name
    raise ValueError('远程文件重定向次数过多')
