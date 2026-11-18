import asyncio
import socket
import unittest
from unittest import mock

from utils import connection_diagnostics as diag


class ConnectionDiagnosticsTest(unittest.TestCase):
    def test_local_listener_distinguishes_running_socket(self):
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', 0))
            listener.listen(1)
            port = listener.getsockname()[1]
            self.assertFalse(diag.local_listener('127.0.0.1', port, False))
            self.assertTrue(diag.local_listener('127.0.0.1', port, True))
        self.assertFalse(diag.local_listener('127.0.0.1', port, True))

    def test_remote_uses_actual_config_and_reports_each_route(self):
        cfg = mock.Mock(force_test_dc=False, dc_redirects={2: '149.154.167.220'},
                        fallback_cfproxy=True, disable_secure=True,
                        cfproxy_worker_domains=['worker.example'])
        calls = []

        async def check(host, domain, **kwargs):
            calls.append((host, domain, kwargs))
            return 'timeout' if domain == 'kws2.cf.example' else 'ok'

        balancer = mock.Mock()
        balancer.get_domains_for_dc.return_value = iter(['cf.example', 'other.example'])
        with mock.patch.object(diag, 'proxy_config', cfg), \
                mock.patch.object(diag, 'balancer', balancer), \
                mock.patch.object(diag, '_check_ws', side_effect=check), \
                mock.patch.object(diag, '_check_tcp', new=mock.AsyncMock(return_value='ok')):
            result = asyncio.run(diag._remote_checks())
        self.assertEqual(result, {'direct': 'ok', 'cf': 'timeout', 'worker': 'ok', 'tcp': 'ok'})
        self.assertEqual(calls[0][0], '149.154.167.220')
        self.assertEqual(calls[1][0], 'kws2.cf.example')
        self.assertFalse(calls[1][2]['secure'])
        self.assertIn('dc=2', calls[2][2]['path'])
        self.assertFalse(calls[2][2]['secure'])

    def test_websocket_failure_is_reported_and_success_is_closed(self):
        ws = mock.Mock()
        ws.close = mock.AsyncMock()
        with mock.patch.object(diag.RawWebSocket, 'connect', new=mock.AsyncMock(return_value=ws)):
            self.assertEqual(asyncio.run(diag._check_ws('host', 'domain')), 'ok')
        ws.close.assert_awaited_once()
        with mock.patch.object(diag.RawWebSocket, 'connect', new=mock.AsyncMock(side_effect=TimeoutError)):
            self.assertEqual(asyncio.run(diag._check_ws('host', 'domain')), 'timeout')


if __name__ == '__main__':
    unittest.main()
