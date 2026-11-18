import unittest
from unittest import mock

from utils import tray_common


class CheckUpdateAsyncTest(unittest.TestCase):
    def test_retries_and_notifies_once_per_version(self):
        statuses = [
            {'has_update': False, 'error': 'offline'},
            {'has_update': True, 'latest': '2.0.0', 'html_url': 'https://x.invalid/r'},
            {'has_update': True, 'latest': '2.0.0', 'html_url': 'https://x.invalid/r'},
            {'has_update': True, 'latest': '2.1.0', 'html_url': 'https://x.invalid/r2'},
        ]
        waits = []
        seen = []
        exiting = [False]

        def wait(seconds):
            waits.append(seconds)
            if len(waits) == 5:
                exiting[0] = True

        with mock.patch('utils.update_check.run_check') as check, \
                mock.patch('utils.update_check.get_status', side_effect=statuses):
            tray_common._update_check_loop(
                {'check_updates': True}, lambda: exiting[0],
                lambda version, url: seen.append((version, url)), wait=wait,
            )
        self.assertEqual(check.call_count, 4)
        self.assertEqual(waits, [1.5, 3600, 3600, 3600, 3600])
        self.assertEqual(seen, [('2.0.0', 'https://x.invalid/r'),
                                ('2.1.0', 'https://x.invalid/r2')])

    def test_respects_changes_to_setting_during_runtime(self):
        cfg = {'check_updates': False}
        waits = []
        exiting = [False]

        def wait(seconds):
            waits.append(seconds)
            if len(waits) == 2:
                cfg['check_updates'] = True
            elif len(waits) == 3:
                exiting[0] = True

        with mock.patch('utils.update_check.run_check') as check, \
                mock.patch('utils.update_check.get_status', return_value={'has_update': False}):
            tray_common._update_check_loop(cfg, lambda: exiting[0], lambda v, u: None, wait=wait)
        check.assert_called_once()


if __name__ == '__main__':
    unittest.main()
