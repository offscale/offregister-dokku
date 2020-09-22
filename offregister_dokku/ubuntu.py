from sys import version

from offutils.util import iteritems

if version[0] == "2":
    from cStringIO import StringIO

else:
    from io import StringIO

from os import environ, path

from offregister_fab_utils.git import clone_or_update, url_to_git_dict
from offutils import it_consumes
from pkg_resources import resource_filename

from fabric.api import sudo, run
from fabric.contrib.files import append, exists, put, upload_template

from offregister_fab_utils.apt import apt_depends
from offregister_fab_utils.fs import cmd_avail
from offregister_fab_utils.ubuntu import docker


def step0(domain, *args, **kwargs):
    key_file = "/root/.ssh/id_rsa.pub"
    config = {
        "DOKKU_HOSTNAME": ("hostname", domain),
        "DOKKU_KEY_FILE": ("key_file", key_file),
        "DOKKU_SKIP_KEY_FILE": ("skip_key_file", False),
        "DOKKU_VHOST_ENABLE": ("vhost_enable", False),
        "DOKKU_WEB_CONFIG": ("web_config", False),
    }
    create_static = kwargs.get("create_static_page", True)
    static_git_url = kwargs.get(
        "static_git", environ.get("DOKKU_STATIC_GIT", environ.get("STATIC_GIT"))
    )

    local_pubkey = kwargs.get("PUBLIC_KEY_PATH") or environ.get(
        "DOKKU_PUBLIC_KEY_PATH", environ["PUBLIC_KEY_PATH"]
    )

    if not cmd_avail("docker"):
        docker.install_0()
        # docker.dockeruser_1()
        docker.serve_2()

    put(StringIO("pZPlHOkV649DCepEwf9G"), "/tmp/passwd")

    if not cmd_avail("dokku"):  # is_installed('dokku'):
        run("wget -qN https://packagecloud.io/gpg.key")
        sudo("apt-key add gpg.key")
        append(
            "/etc/apt/sources.list.d/dokku.list",
            "deb https://packagecloud.io/dokku/dokku/ubuntu/ trusty main",
            use_sudo=True,
        )

        put(
            StringIO(
                "\n".join(
                    "{com} {com}/{var} {type} {val}".format(
                        com="dokku",
                        var=v[0],
                        val=str(v[1]).lower() if type(v[1]) is type(bool) else v[1],
                        type=(
                            lambda t: {
                                type(True): "boolean",
                                type(""): "string",
                                type(str): "string",
                            }.get(t, t)
                        )(type(v[1])),
                    )
                    for k, v in iteritems(config)
                    if v[1] is not None
                )
            ),
            "/tmp/dokku-debconf",
        )

        sudo("debconf-set-selections /tmp/dokku-debconf")
        if not exists(key_file):
            sudo(
                'ssh-keygen -t rsa -b 4096 -f {key_file} -N ""'.format(
                    key_file=key_file
                )
            )

        apt_depends("dokku")
        sudo("dokku plugin:install-dependencies --core")
        put(local_pubkey, key_file)
        sudo("sshcommand acl-add dokku domain {key_file}".format(key_file=key_file))
        return "installed dokku"

    if create_static:
        if run("getent passwd static", quiet=True, warn_only=True).failed:
            sudo("adduser static --disabled-password")
            sudo("mkdir /home/static/sites/", user="static")

        upload_template(
            path.join(
                path.dirname(resource_filename("offregister_dokku", "__init__.py")),
                "data",
                "static_sites.conf",
            ),
            "/etc/nginx/conf.d/static_sites.conf",
            use_sudo=True,
        )

        if sudo("service nginx status").endswith("stop/waiting"):
            sudo("service nginx start")
        else:
            sudo("service nginx reload")

        # TODO: Abstract this out into a different module, and allow for multiple domains
        if static_git_url:
            ipv4 = "/home/static/sites/{public_ipv4}".format(
                public_ipv4=kwargs["public_ipv4"]
            )
            if exists(ipv4):
                sudo("rm -rf {ipv4}".format(ipv4=ipv4))
            sudo("mkdir -p {ipv4}".format(ipv4=ipv4), user="static")
            if domain:
                domain = "/home/static/sites/{domain}".format(domain=domain)
                if not exists(domain):
                    sudo(
                        "ln -s {ipv4} {domain}".format(ipv4=ipv4, domain=domain),
                        user="static",
                    )
            xip = "{ipv4}.xip.io".format(ipv4=ipv4)
            if not exists(xip):
                sudo("ln -s {ipv4} {xip}".format(ipv4=ipv4, xip=xip), user="static")

            if static_git_url:
                apt_depends("git")

                if isinstance(static_git_url, str):
                    clone_or_update(**url_to_git_dict(static_git_url))
                else:
                    clone_or_update(to_dir=ipv4, **static_git_url)

    return "installed dokku [already]"


def step1(*args, **kwargs):
    run("echo serve")
    return "served dokku"
