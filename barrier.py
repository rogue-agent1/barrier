#!/usr/bin/env python3
"""barrier: Cyclic barrier synchronization primitive."""
import threading, sys, time

class Barrier:
    def __init__(self, parties):
        self.parties = parties
        self._count = 0
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._generation = 0

    def wait(self, timeout=5):
        with self._lock:
            gen = self._generation
            self._count += 1
            if self._count == self.parties:
                self._count = 0
                self._generation += 1
                self._event.set()
                self._event = threading.Event()
                return True  # Leader
        evt = self._event
        if not evt.wait(timeout):
            raise TimeoutError("Barrier timeout")
        return False  # Follower

    def reset(self):
        with self._lock:
            self._count = 0
            self._generation += 1
            self._event.set()
            self._event = threading.Event()

def test():
    b = Barrier(3)
    order = []
    lock = threading.Lock()

    def worker(n):
        with lock:
            order.append(("before", n))
        is_leader = b.wait()
        with lock:
            order.append(("after", n, is_leader))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
    for t in threads: t.start()
    for t in threads: t.join()

    befores = [e for e in order if e[0] == "before"]
    afters = [e for e in order if e[0] == "after"]
    assert len(befores) == 3
    assert len(afters) == 3
    # Exactly one leader
    leaders = [e for e in afters if e[2]]
    assert len(leaders) == 1

    # Cyclic — can reuse
    order.clear()
    def worker2(n):
        b.wait()
        with lock:
            order.append(("round1", n))
        b.wait()
        with lock:
            order.append(("round2", n))

    threads = [threading.Thread(target=worker2, args=(i,)) for i in range(3)]
    for t in threads: t.start()
    for t in threads: t.join()
    r1 = [e for e in order if e[0] == "round1"]
    r2 = [e for e in order if e[0] == "round2"]
    assert len(r1) == 3
    assert len(r2) == 3
    print("All tests passed!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test": test()
    else: print("Usage: barrier.py test")
