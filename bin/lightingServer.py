#!/usr/bin/env python
from home import lightingControl as lc
import logging

from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import ServerFactory
from twisted.internet import task
from twisted.internet import reactor

logging.basicConfig()

class lightingProtocol(LineReceiver):
    def __init__(self):
        self.logger = logging.getLogger('LightingProtocol')
        self.logger.setLevel(logging.DEBUG)

    def lineReceived(self, line):
        sline = line.split()
        if sline[0] == "read":
            self.logger.debug("Sending Data")

class lightingServer(ServerFactory):
    protocol = lightingProtocol

    def __init__(self):
        self.p = "poop"


if __name__ == "__main__":
    lights = lc.lightingControl()
    light_loop = task.LoopingCall(lights.set_lights)
    light_loop.start(30)

    reactor.listenTCP(50000, lightingServer())
    reactor.run()
