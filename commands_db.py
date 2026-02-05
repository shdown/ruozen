# (c) 2026 shdown
# This code is licensed under MIT license (see LICENSE.MIT for details)

from commands import command_decorator as cmd
import subprocess
import datetime
import shlex


def _run(argv):
    shell_cmd = ' '.join(shlex.quote(s) for s in argv)
    subprocess.run(f'{shell_cmd} &', shell=True, check=False)


@cmd('откро[йю] редактор')
def handler(m):
    _run(['gvim'])


@cmd('откро[йю] википеди[ийюя] (.*)')
def handler(m):
    _run(['xdg-open', 'https://ru.wikipedia.org/wiki/' + m.group(1)])


@cmd('время')
def handler(m):
    time_str = datetime.datetime.now().strftime('%H:%M')
    return f'Сейчас {time_str}'
