import asyncio

from typing import Callable, Coroutine

# идея в том, что рабочие разбирают очередь из задач
# каждый рабочий берёт задачу, и начинает её выполнять в цикле
# пока задача не выкинет StopWork
class WorkerPool:
    class StopWork(Exception): ...

    def __init__(self, workers):
        self.workers = workers
        self.q: asyncio.Queue[Callable[[], Coroutine]] = asyncio.Queue()

        self._make_tasks()

    def _make_tasks(self):
        self._tasks = [
            asyncio.create_task(self._worker(), name=f'worker_{i}')
            for i in range(self.workers)
        ]

    async def _worker(self):
        try:
            while True:
                job_supplier = await self.q.get()

                try:
                    while True:
                        # получаем корутину, ждём её выполнения
                        await (job_supplier())
                except WorkerPool.StopWork: ...
        except asyncio.CancelledError: ...

    async def add_job(self, job_supplier: Callable[[], Coroutine]):
        await self.q.put(job_supplier)

    async def run(self):
        for t in self._tasks:
            await t

    async def close(self):
        for t in self._tasks:
            t.cancel()
