#!/usr/bin/env python
from subprocess import check_output, STDOUT, CalledProcessError
from json import loads
import sys


class InspectParser(object):
    def __init__(self, container):
        self.container = container
        self.data = self.get_data(self.container)

    def get_data(self, container):
        try:
            data = loads(check_output("docker inspect {}".format(container),
                         stderr=STDOUT, shell=True))
        except CalledProcessError as e:
            sys.stderr.write(e.output)
            sys.exit(1)
        return data[0]

    def get_fact(self, path):
        keys = path.split("/")
        val = None

        for key in keys:
            if val:
                val = val.get(key)
            else:
                val = self.data.get(key)

        return val

    def get_image(self):
        image = self.get_fact('Config/Image')
        return image

    def get_command(self):
        command = self.get_fact('Config/Cmd')
        if command:
            return ' '.join(command)

    def getopt_env(self):
        env_options = []
        env = self.get_fact('Config/Env')
        if env:
            for var in env:
                env_options.append('--env {}'.format(var))
        return ' '.join(env_options)

    def getopt_extrahosts(self):
        extra_hosts = self.get_fact('HostConfig/ExtraHosts')
        if extra_hosts:
            return ' '.join(['--add-host {}'.format(host) for host in extra_hosts])

    def getopt_labels(self):
        labels = self.get_fact('Config/Labels')
        if labels:
            return ' '.join(['--label {}={}'.format(k, v) for k, v in labels.iteritems()])

    def getopt_links(self):
        links_options = []
        links = self.get_fact('HostConfig/Links')
        if links:
            for link in links:
                src, dst = link.split(':')
                src = src.strip('/')
                dst = dst.split('/')[1]
                links_options.append('--link {}:{}'.format(src, dst))
        return ' '.join(links_options)

    def getopt_ports(self):
        ports_options = []
        ports = self.get_fact('NetworkSettings/Ports')
        if ports:
            for int, ext in ports.iteritems():
                if ext:
                    ext_ip = ext[0].get('HostIp')
                    ext_port = ext[0].get('HostPort')
                    ports_options.append("-p {}:{}:{}".format(ext_ip, ext_port, int))
                else:
                    ports_options.append("--expose {}".format(int))
        return ' '.join(ports_options)

    def getopt_restart(self):
        policy_data = self.get_fact('HostConfig/RestartPolicy')
        policy = policy_data.get('Name')
        if policy != "no":
            if policy == "on-failure":
                return '--restart {}:{}'.format(policy, policy_data.get('MaximumRetryCount'))
            return '--restart {}'.format(policy)

    def getopt_volumes(self):
        volumes_options = []
        volumes = self.get_fact('HostConfig/Binds')
        if volumes:
            for volume in volumes:
                volumes_options.append('-v {}'.format(volume))
        return ' '.join(volumes_options)

    def getopt_detached(self):
        signs = ['Config/AttachStdin', 'Config/AttachStdout', 'Config/AttachStderr']
        if not any([self.get_fact(sign) for sign in signs]):
            return '-d'

    def getopt_flags(self):
        flags_options = []
        flags = {
            'Config/Tty': '-t',
            'Config/OpenStdin': '-i',
            'HostConfig/AutoRemove': '--rm',
            'HostConfig/Privileged': '--privileged',
        }

        for path, flag in flags.iteritems():
            if self.get_fact(path):
                flags_options.append(flag)

        return ' '.join(flags_options)

    def parse(self):
        if self.get_fact('RootFS'):
            sys.stderr.write("Error: It's an image, not a container: {}".format(self.container))
            sys.exit(1)

        options = []
        for attr in dir(self):
            if attr.startswith('getopt_'):
                result = getattr(self, attr)()
                if result:
                    options.append(result)

        image = self.get_image()
        command = self.get_command()

        return 'docker run {} \\\n\t {} {}'.format(' \\\n\t'.join(options), image, command if command else '')


def main():
    parser = InspectParser(sys.argv[1])
    print(parser.parse())


if __name__ == '__main__':
    main()

#  vim: set et fenc=utf-8 ft=python sts=4 sw=4 ts=4 tw=79 :
