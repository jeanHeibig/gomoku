import multiprocessing
import time

def run_bot(bot_func, position, pendule, timeout=1.0):
    def target(q):
        try:
            move = bot_func(position, pendule)
            q.put(move)
        except:
            q.put(None)

    q = multiprocessing.Queue()
    p = multiprocessing.Process(target=target, args=(q,))
    p.start()
    p.join(timeout)

    if p.is_alive():
        p.terminate()
        return None, timeout

    if q.empty():
        return None, timeout

    return q.get(), timeout
