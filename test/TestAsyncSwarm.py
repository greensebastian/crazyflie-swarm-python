from unittest import TestCase
from AsyncSwarm import AsyncSwarm
from CFUtil import CFUtil


class TestAsyncSwarm(TestCase):
    def setUp(self):
        self.swarm = AsyncSwarm((0, 1, 2, 3, 4))
        pos = {}
        pos[CFUtil.URI1] = (1, 5, 1)
        pos[CFUtil.URI2] = (2, 4, 3)
        pos[CFUtil.URI3] = (3, 3, 2)
        pos[CFUtil.URI4] = (4, 2, 5)
        pos[CFUtil.URI5] = (5, 1, 4)

        for uri in CFUtil.URIS_DEFAULT:
            data = CFUtil.generate_drone(name=uri, pos=pos[uri], vel=(0, 0, 0))
            self.swarm.log_callback(uri=uri, timestamp=1, data=data[uri], logconf=None)

    def tearDown(self):
        pass

    def test_get_relative_order(self):
        res = self.swarm.get_relative_order()
        print(res)

