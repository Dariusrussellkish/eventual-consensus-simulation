import logging
from copy import deepcopy
from numpy import random, mean, floor, ceil, log
import numpy as np


def __filter_list__(to_filter, remove=None):
    if remove is None:
        remove = [None]
    return list(x for x in to_filter if x not in remove)


def __mean_trim__(l1, f):
    return mean(__trim__(l1, f))


def __trim__(l1, f):
    sorted_l1 = deepcopy(l1)
    sorted_l1.sort()
    if f != 0:
        trimmed_list = np.array(sorted_l1)[f:-f]
    else:
        trimmed_list = np.array(sorted_l1)
    return trimmed_list


def __c__(m, k):
    return floor((m-1)/float(k)) + 1


def __select__(l1, k):
    return [l1[i] for i in range(0, len(l1), k)]


def __not_none_union__(l1, l2):
    return l1 + l2


class AlgorithmJACM86:
    logger = logging.getLogger('Algo-JACM86')

    def __init__(self, K, servers, server_id, f, eps, **kwargs):
        self.K = K
        self.nServers = servers
        self.server_id = server_id
        self.v = random.uniform(0, K)
        self.has_valid_n = servers >= 5 * f + 1
        self.p = 0
        self.f = f
        self.eps = eps
        self._reset()
        self.supports_byzantine = servers >= 5 * f + 1
        self.a = 0.5 * ((servers - 5 * f) / (2 * (servers - f)))
        self.p_end = None
        self.done_servers = [False for _ in range(servers)]
        AlgorithmJACM86.logger.info(
            f"Server {self.server_id} will terminate after {self.p_end} phases")

    def _reset(self):
        self.R = list([None for _ in range(self.nServers)])
        self.R[self.server_id] = self.v

    def is_done(self):
        if self.p_end is None:
            return False
        return self.p > self.p_end

    def process_message(self, message):
        s_id = message['id']
        if message['is_done']:
            self.done_servers[s_id] = True

        if message['p'] == self.p and self.R[s_id] is None:
            self.R[s_id] = message['v']

        filtered_R = __filter_list__(self.R)
        if len(filtered_R) + sum(self.done_servers) >= self.nServers - self.f:
            for i, v in enumerate(self.done_servers):
                if v:
                    self.R[i] = 0
            filtered_R = __filter_list__(self.R)
            if self.p == 0:
                self.v = __mean_trim__(filtered_R, 2 * self.f)
                dV = max(filtered_R) - min(filtered_R)
                self.p_end = ceil(log(dV/self.eps)/log(__c__(self.nServers - 3 * self.f, 2 * self.f)))
                self.p += 1
                self._reset()
                AlgorithmJACM86.logger.info(
                    f"Server {self.server_id} accepting update via mean trim, phase is now {self.p}")
                return True
            elif self.p <= self.p_end:
                self.v = mean(__select__(__trim__(filtered_R, self.f), 2 * self.f))
                self.p += 1
                self._reset()
                AlgorithmJACM86.logger.info(
                    f"Server {self.server_id} accepting update via mean select trim, phase is now {self.p}")
                return True
        return False

    def get_internal_state(self):
        return {
            'v': self.v,
            'p': self.p,
        }