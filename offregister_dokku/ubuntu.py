from types import BooleanType

from fabric.api import sudo, run
from fabric.contrib.files import append, exists

from offregister_fab_utils.apt import apt_depends
from offregister_fab_utils.fs import cmd_avail


def install(*args, **kwargs):
    key_file = '/root/.ssh/id_rsa.pub'
    config = {
        'DOKKU_HOSTNAME': ('hostname', kwargs['domain']),
        'DOKKU_KEY_FILE': ('key_file', key_file),
        'DOKKU_SKIP_KEY_FILE': ('skip_key_file', False),
        'DOKKU_VHOST_ENABLE': ('vhost_enable', False),
        'DOKKU_WEB_CONFIG': ('web_config', False)
    }

    if not cmd_avail('docker'):
        run('wget -qN https://get.docker.com -o docker_install.sh')
        run('sh docker_install.sh')
    if not cmd_avail('dokku'):  # is_installed('dokku'):
        run('wget -qN https://packagecloud.io/gpg.key')
        sudo('apt-key add gpg.key')
        append('/etc/apt/sources.list.d/dokku.list',
               'deb https://packagecloud.io/dokku/dokku/ubuntu/ trusty main', use_sudo=True)

        run('echo "{}" > /tmp/dokku-debconf'.format(
            '\n'.join('{com} {com}/{var} {type} {val}'.format(
                com='dokku', var=v[0], val=str(v[1]).lower() if type(v[1]) is BooleanType else v[1], type=(
                    lambda t: {
                        type(True): 'boolean', type(''): 'string', type(unicode): 'string'
                    }.get(t, t))(type(v[1])))
                      for k, v in config.iteritems() if v[1] is not None)
        ))

        sudo('debconf-set-selections /tmp/dokku-debconf')
        if not exists(key_file):
            sudo('ssh-keygen -t rsa -b 4096 -f {key_file} -N ""'.format(key_file=key_file))

        apt_depends('dokku')
        sudo('dokku plugin:install-dependencies --core')
        return 'installed dokku'
    return 'installed dokku [already]'


def serve(*args, **kwargs):
    run('echo serve')
    return 'served dokku'
