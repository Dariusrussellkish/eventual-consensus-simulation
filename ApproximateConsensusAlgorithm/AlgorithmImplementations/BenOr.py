import logging
import random
from collections import defaultdict
from numpy import unique


def __flip_coin__():
    return int(random.getrandbits(1))


def __filter_list__(to_filter, remove=None):
    if remove is None:
        remove = [None]
    return list(x for x in to_filter if x not in remove)


def __check_majority__(l1, ignore=None):
    if ignore is None:
        ignore = [None]

    filtered_list = __filter_list__(l1, remove=ignore)
    vals, counts = unique(filtered_list, return_counts=True)
    for val, count in zip(vals, counts):
        if count > len(l1)/2.0:
            return int(val)
    return None


class AlgorithmBenOr:
    logger = logging.getLogger('Algo-BenOr')

    def __init__(self, servers, server_id, f, eps, **kwargs):
        self.nServers = servers
        self.server_id = server_id
        self.v = __flip_coin__()
        self.w = None
        self.p = 0
        self.phase = 1
        self.f = f
        self.supports_byzantine = False
        self.has_valid_n = servers > 2 * f
        self.eps = eps
        self.futures = defaultdict(list)
        self._reset()
        self.requires_synchronous_update_broadcast = True
        self.isDone = False

    def _reset(self):
        self.R = list([None for _ in range(self.nServers)])
        self.S = list([None for _ in range(self.nServers)])
        self.R[self.server_id] = self.v
        self.S[self.server_id] = self.v
        self.w = None

    def is_done(self):
        return self.isDone

    def process_message(self, message):
        s_id = message['id']

        if self.futures[self.p]:
            for i in range(len(self.futures[self.p])):
                message = self.futures[self.p].pop()
                if message['phase'] == 1:
                    self.R[s_id] = message['v']
                else:
                    self.S[s_id] = message['w']

        if message['p'] > self.p:
            self.futures[message['p']].append(message)
        if message['p'] == self.p and message['phase'] == 1:
            AlgorithmBenOr.logger.info(
                f"Server {self.server_id} received p={message['p']} phase 1 from {s_id}")
            self.R[s_id] = message['v']
        elif message['p'] == self.p and message['phase'] == 2:
            AlgorithmBenOr.logger.info(
                f"Server {self.server_id} received p={message['p']} phase 2 from {s_id}")
            self.S[s_id] = message['w']

        filtered_R = __filter_list__(self.R)
        filtered_S = __filter_list__(self.S)
        if self.phase == 1 and len(filtered_R) >= self.nServers - self.f:
            majority_value = __check_majority__(self.R)
            if majority_value is not None:
                self.w = majority_value
            else:
                self.w = -1
            self.phase = 2
        elif self.phase == 2 and len(filtered_S) >= self.nServers - self.f:
            values = __filter_list__(self.S, remove=[None, -1])
            if values:
                self.v = values[0]
                if len(list(x for x in self.S if x == self.v)) > self.f:
                    self.isDone = True
            else:
                self.v = __flip_coin__()
            self.phase = 1
            self._reset()
            AlgorithmBenOr.logger.info(
                f"Server {self.server_id} accepted update, phase is now {self.p}")
            self.p += 1
            return True
        return False

    def get_internal_state(self):
        return {
            "phase": self.phase,
            "v": self.v,
            "p": int(self.p),
            "w": self.w
        }
