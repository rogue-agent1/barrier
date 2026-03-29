#!/usr/bin/env python3
"""barrier - Thread barrier and countdown latch implementations."""
import sys, threading

class Barrier:
    def __init__(self, parties):
        self.parties = parties
        self.count = 0
        self.generation = 0
        self.lock = threading.Lock()
        self.cv = threading.Condition(self.lock)

    def wait(self, timeout=None):
        with self.cv:
            gen = self.generation
            self.count += 1
            if self.count == self.parties:
                self.count = 0
                self.generation += 1
                self.cv.notify_all()
                return True
            while gen == self.generation:
                if not self.cv.wait(timeout=timeout):
                    return False
            return True

class CountdownLatch:
    def __init__(self, count):
        self.count = count
        self.lock = threading.Lock()
        self.cv = threading.Condition(self.lock)

    def count_down(self):
        with self.cv:
            self.count -= 1
            if self.count <= 0:
                self.cv.notify_all()

    def await_(self, timeout=None):
        with self.cv:
            if self.count <= 0:
                return True
            return self.cv.wait(timeout=timeout)

class CyclicBarrier:
    def __init__(self, parties, action=None):
        self.parties = parties
        self.action = action
        self.count = 0
        self.lock = threading.Lock()
        self.cv = threading.Condition(self.lock)
        self.generation = 0

    def wait(self):
        with self.cv:
            gen = self.generation
            self.count += 1
            if self.count == self.parties:
                if self.action:
                    self.action()
                self.count = 0
                self.generation += 1
                self.cv.notify_all()
                return 0
            idx = self.count
            while gen == self.generation:
                self.cv.wait()
            return idx

def test():
    order = []
    b = Barrier(3)
    def worker(n):
        order.append(f"pre_{n}")
        b.wait()
        order.append(f"post_{n}")
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert len([x for x in order if x.startswith("pre_")]) == 3
    assert len([x for x in order if x.startswith("post_")]) == 3
    latch = CountdownLatch(3)
    result = []
    def waiter():
        latch.await_()
        result.append("done")
    t = threading.Thread(target=waiter)
    t.start()
    latch.count_down()
    latch.count_down()
    latch.count_down()
    t.join(timeout=2)
    assert result == ["done"]
    actions = []
    cb = CyclicBarrier(2, action=lambda: actions.append("barrier!"))
    def cb_worker():
        cb.wait()
    t1 = threading.Thread(target=cb_worker)
    t2 = threading.Thread(target=cb_worker)
    t1.start(); t2.start()
    t1.join(); t2.join()
    assert actions == ["barrier!"]
    print("All tests passed!")

if __name__ == "__main__":
    test() if "--test" in sys.argv else print("barrier: Thread barriers. Use --test")
