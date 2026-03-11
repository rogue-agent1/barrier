#!/usr/bin/env python3
"""Barrier — synchronization primitive for parallel phases."""
import threading, time, sys

class Barrier:
    def __init__(self, parties):
        self.parties = parties; self._count = 0; self._generation = 0
        self._lock = threading.Lock(); self._cond = threading.Condition(self._lock)
    def wait(self):
        with self._cond:
            gen = self._generation; self._count += 1
            if self._count == self.parties:
                self._count = 0; self._generation += 1
                self._cond.notify_all(); return True  # leader
            while gen == self._generation: self._cond.wait()
            return False

class CyclicBarrier(Barrier):
    def __init__(self, parties, action=None):
        super().__init__(parties); self.action = action
    def wait(self):
        is_leader = super().wait()
        if is_leader and self.action: self.action()
        return is_leader

if __name__ == "__main__":
    results = {i: [] for i in range(3)}
    b = CyclicBarrier(3, action=lambda: print("--- Phase complete ---"))
    def worker(wid):
        for phase in range(3):
            time.sleep(0.01 * (wid + 1))
            results[wid].append(f"phase-{phase}")
            b.wait()
    threads = [threading.Thread(target=worker, args=(i,)) for i in range(3)]
    for t in threads: t.start()
    for t in threads: t.join()
    for wid, res in results.items(): print(f"Worker {wid}: {res}")
