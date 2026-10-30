import os
import unittest
from unittest.mock import patch

from backend import serve


class DeploymentEntrypointTests(unittest.TestCase):
    def test_default_command_is_safe_and_platform_port_compatible(self):
        with patch.dict(os.environ, {}, clear=True):
            command = serve.build_command()

        self.assertEqual(command[0:2], ["uvicorn", "backend.app.main:app"])
        self.assertEqual(command[command.index("--host") + 1], "0.0.0.0")
        self.assertEqual(command[command.index("--port") + 1], "8000")
        self.assertEqual(command[command.index("--workers") + 1], "1")
        self.assertIn("--access-log", command)
        self.assertIn("--no-proxy-headers", command)
        self.assertNotIn("--forwarded-allow-ips", command)

    def test_explicit_runtime_and_reviewed_proxy_settings_are_forwarded(self):
        environment = {
            "HOST": "127.0.0.1",
            "PORT": "49152",
            "WEB_CONCURRENCY": "3",
            "LOG_LEVEL": "warning",
            "UVICORN_ACCESS_LOG": "0",
            "TRUSTED_PROXY_HEADERS": "1",
            "FORWARDED_ALLOW_IPS": "10.0.0.0/8,127.0.0.1",
        }
        with patch.dict(os.environ, environment, clear=True):
            command = serve.build_command()

        self.assertEqual(command[command.index("--host") + 1], "127.0.0.1")
        self.assertEqual(command[command.index("--port") + 1], "49152")
        self.assertEqual(command[command.index("--workers") + 1], "3")
        self.assertEqual(command[command.index("--log-level") + 1], "warning")
        self.assertIn("--no-access-log", command)
        self.assertIn("--proxy-headers", command)
        self.assertEqual(
            command[command.index("--forwarded-allow-ips") + 1],
            "10.0.0.0/8,127.0.0.1",
        )

    def test_proxy_headers_require_an_explicit_allow_list(self):
        with patch.dict(
            os.environ,
            {"TRUSTED_PROXY_HEADERS": "1"},
            clear=True,
        ):
            with self.assertRaisesRegex(ValueError, "FORWARDED_ALLOW_IPS"):
                serve.build_command()

    def test_main_replaces_the_process_with_the_built_command(self):
        command = ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
        with (
            patch.object(serve, "build_command", return_value=command),
            patch.object(serve.os, "execvp") as execvp,
        ):
            serve.main()

        execvp.assert_called_once_with("uvicorn", command)


if __name__ == "__main__":
    unittest.main()
