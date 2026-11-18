"""Small, non-destructive connectivity checks for the Windows tray menu."""
from __future__ import annotations

import asyncio
import socket
from urllib.parse import urlencode

from proxy.balancer import balancer
from proxy.config import proxy_config
from proxy.raw_websocket import RawWebSocket, WsHandshakeError
from proxy.utils import DC_TEST_IPS, DC_DEFAULT_IPS, WS_PATH, WS_PATH_TEST, ws_domains


def local_listener(host, port, running):
    if not running:
        return False
    host = '127.0.0.1' if host in ('0.0.0.0', '', '::') else host
    try:
        with socket.create_connection((host, port), timeout=2):
            return True
    except OSError:
        return False


async def _check_ws(host, domain, *, secure=True, path=WS_PATH):
    try:
        ws = await asyncio.wait_for(
            RawWebSocket.connect(host, domain, timeout=6, path=path, secure=secure),
            timeout=8,
        )
        try:
            await asyncio.wait_for(ws.close(), timeout=2)
        except (OSError, asyncio.TimeoutError):
            pass
        return 'ok'
    except (TimeoutError, asyncio.TimeoutError):
        return 'timeout'
    except WsHandshakeError:
        return 'handshake'
    except OSError:
        return 'network'
    except Exception:
        return 'error'


async def _check_tcp(host):
    try:
        _, writer = await asyncio.wait_for(asyncio.open_connection(host, 443), timeout=6)
        writer.close()
        await writer.wait_closed()
        return 'ok'
    except (TimeoutError, asyncio.TimeoutError):
        return 'timeout'
    except OSError:
        return 'network'


async def _remote_checks():
    # DC2 is a representative route; media and other DCs can behave differently.
    test = proxy_config.force_test_dc
    direct_ip = proxy_config.dc_redirects.get(2)
    tasks = {'tcp': _check_tcp((DC_TEST_IPS if test else DC_DEFAULT_IPS)[2])}
    if direct_ip:
        tasks['direct'] = _check_ws(direct_ip, ws_domains(2, False)[0],
                                    path=WS_PATH_TEST if test else WS_PATH)
    domains = list(balancer.get_domains_for_dc(2)) if proxy_config.fallback_cfproxy and not test else []
    if domains:
        host = f'kws2.{domains[0]}'
        tasks['cf'] = _check_ws(host, host, secure=not proxy_config.disable_secure)
    workers = proxy_config.cfproxy_worker_domains
    if workers:
        host = workers[0]
        path = WS_PATH + '?' + urlencode({'dst': (DC_TEST_IPS if test else DC_DEFAULT_IPS)[2], 'dc': 2, 'media': 0})
        tasks['worker'] = _check_ws(host, host, secure=not proxy_config.disable_secure, path=path)
    results = {'direct': 'skipped', 'cf': 'skipped', 'worker': 'skipped', 'tcp': 'skipped'}
    if tasks:
        values = await asyncio.gather(*tasks.values())
        results.update(zip(tasks, values))
    return results


def diagnose_connection(host, port, running):
    local = local_listener(host, port, running)
    remote = asyncio.run(_remote_checks())
    return {'local': 'ok' if local else 'unavailable', **remote,
            'no_secure': proxy_config.disable_secure}
