import asyncio
from collections import deque

task_queue = deque()
task_status = {}
semaphore = asyncio.Semaphore(20)

async def broadcast_status(manager, task_id, status):
    task_status[task_id] = status
    await manager.broadcast({"task_id": task_id, "status": status})

async def worker():
    from main import manager
    while True:
        if task_queue:
            task_id, task_func, task_args = task_queue.popleft()
            async with semaphore:
                try:
                    await broadcast_status(manager, task_id, "in_progress")
                    await task_func(*task_args)
                    await broadcast_status(manager, task_id, "completed")
                except Exception as e:
                    task_status[task_id] = "failed"
                    await broadcast_status(manager, task_id, "failed")
                    print(f"Task {task_id} failed: {str(e)}")
        await asyncio.sleep(0.5)

def add_task(task_id, task_func, *task_args):
    task_queue.append((task_id, task_func, task_args))
    task_status[task_id] = "queued"

def call_status(task_id):
    return task_status.get(task_id, "not_found")

def start_worker():
    loop = asyncio.get_event_loop()
    loop.create_task(worker())