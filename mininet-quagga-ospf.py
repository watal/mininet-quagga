#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
以下のようなルータ二台，ホスト二台のシンプルなネットワーク構成

    H1 - R1 - R2 - H2

それぞれのネットワークアドレス・接続インターフェースは以下の通り

    R1-eth1 - R2-eth1 (IP: 192.168.0.0/24)
    H1-eth1 - R1-eth2 (IP: 192.168.1.0/24)
    H1-eth1 - R2-eth2 (IP: 192.168.2.0/24)
'''

import os
import time
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI


class LinuxRouter(Node):
    """A Node with IP forwarding enabled."""

    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()


class NetworkTopo(Topo):
    """Two Linux Routers (Quagga) are each connected to a host."""

    def build(self, **_opts):
        # ルータの設定（IPアドレスの末尾にはノード番号を埋め込む）
        r1 = self.addNode('R1', cls=LinuxRouter,
                          ip='192.168.0.1/24')  # r1-eth1
        r2 = self.addNode('R2', cls=LinuxRouter,
                          ip='192.168.0.2/24')  # r2-eth1

        # ホストの設定（IPアドレスの末尾にはノード番号を埋め込む）
        h1 = self.addHost('H1', ip='192.168.1.10/24',
                          defaultRoute='via 192.168.1.1')  # r1-eth2
        h2 = self.addHost('H2', ip='192.168.2.20/24',
                          defaultRoute='via 192.168.2.2')  # r2-eth2

        # R1-R2の接続
        self.addLink(r1, r2, intfName1='R1-eth1', intfName2='R2-eth1')

        # R1-H1の接続
        self.addLink(h1, r1, intfName2='R1-eth2',
                     params2={'ip': '192.168.1.1/24'})

        # R2-H2の接続
        self.addLink(h2, r2, intfName2='R2-eth2',
                     params2={'ip': '192.168.2.2/24'})


def SetQuagga(Router):
    """Start zebra and ospfd."""

    # zebraの起動・起動待ち
    Router.cmd('/usr/local/sbin/zebra -f conf/%s-zebra.conf -d -i /tmp/%s-zebra.pid -z /tmp/%s-zebra.api > logs/%s-zebra-stdout 2>&1'
               % (Router.name, Router.name, Router.name, Router.name))
    Router.waitOutput()

    # ospfdの起動・起動待ち
    Router.cmd('/usr/local/sbin/ospfd -f conf/%s-ospfd.conf -d -i /tmp/%s-ospfd.pid -z /tmp/%s-zebra.api > logs/%s-ospfd-stdout 2>&1'
               % (Router.name, Router.name, Router.name, Router.name), shell=True)
    Router.waitOutput()


def run():
    """Create and test a network."""

    # ネットワーク生成
    net = Mininet(topo=NetworkTopo(), controller=None)
    net.start()

    # Quaggaの設定・起動
    info('*** Launch Quagga on Router:\n')
    r1 = net.getNodeByName('R1')
    SetQuagga(r1)
    r2 = net.getNodeByName('R2')
    SetQuagga(r2)

    # とりあえずCLI立ち上げ
    CLI(net)
    net.stop()
    # zebra・ospfdの停止
    os.system('killall -9 zebra ospfd')


def main():
    setLogLevel('info')
    run()


if __name__ == '__main__':
    main()
