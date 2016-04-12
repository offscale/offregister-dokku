from fabric.api import sudo, run
from fabric.contrib.files import append

from offregister_fab_utils.apt import apt_depends, is_installed, Package
from offregister_fab_utils.fs import cmd_avail


def install(*args, **kwargs):
    if not cmd_avail('docker') or not cmd_avail('dokku'):  # is_installed('dokku'):
        run('wget -nv -O - https://get.docker.com/ | sh')
        run('wget -nv -O - https://packagecloud.io/gpg.key | apt-key add -')
        append('/etc/apt/sources.list.d/dokku.list',
               'deb https://packagecloud.io/dokku/dokku/ubuntu/ trusty main', use_sudo=True)
        apt_depends('dokku')
        sudo('dokku plugin:install-dependencies --core')
        return 'installed dokku'
    return 'installed dokku [already]'


def serve(*args, **kwargs):
    run('echo serve')
    return 'served dokku'
