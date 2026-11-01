"""Wall-clock dates in the same named local zone as the fixture's Node daemon."""
from datetime import datetime
import subprocess
from zoneinfo import ZoneInfo


def local_now(environment):
    name = subprocess.check_output(['node', '-p', 'Intl.DateTimeFormat().resolvedOptions().timeZone'],
                                   env=environment, text=True).strip()
    return datetime.now(ZoneInfo(name))
