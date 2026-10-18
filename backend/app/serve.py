"""Production entry point with a platform-supplied port and proxy trust."""
import os
from pathlib import Path

import uvicorn


APP_UID = 10001
APP_GID = 10001


def prepare_data_directory():
    """Make a platform-mounted data directory writable, then drop root privileges."""
    if os.geteuid() != 0:
        return

    data_directory = Path(os.getenv('MOSAIC_DATA', '/data'))
    data_directory.mkdir(parents=True, exist_ok=True)
    os.chown(data_directory, APP_UID, APP_GID)
    os.setgroups([])
    os.setgid(APP_GID)
    os.setuid(APP_UID)


def configuration():
    return {
        'host': '0.0.0.0',
        'port': int(os.getenv('PORT', '8000')),
        'proxy_headers': True,
        'forwarded_allow_ips': os.getenv('FORWARDED_ALLOW_IPS', '127.0.0.1'),
        'access_log': False,
        'log_level': 'critical',
    }


if __name__ == '__main__':
    prepare_data_directory()
    uvicorn.run('backend.app.main:app', **configuration())
