import asyncio 
from api.api_request import Requests
import aiohttp
import logging 
from asyncio import Semaphore

logger = logging.getLogger(__name__)

class QueueProcessor:
    def __init__(self, api_request, concurrency, request_type):
        self.api_request = api_request
        self.queue = asyncio.Queue()
        self.concurrency = concurrency
        self.worker_tasks = []
        self.processed_queue = set()
        self.response_list = []
        self.request_type = request_type
# Adding to queue can add it as a list or single items
    async def add_to_queue(self, data):
        if isinstance(data, list):
            for item in data:
                await self.queue.put((item, 1))
        else:       
            await self.queue.put((data, 1))

# Worker will take a task from the queue and process it by sending a request to the API, if it failes after the request max retry it will add it back into the queue
    async def worker(self, session):
        while True:
            try:
                data, attempt = await self.queue.get()
                request_id = f"{data['name']}_{data['data']['row']}_{data['data']['column']}"

                if request_id in self.processed_queue:
                    logger.info(f'Skipping duplicate request {request_id}')
                    self.queue.task_done()
                    continue

                await asyncio.sleep(0.5)
                success, response_data = await self.api_request.planet_request(session, data, attempt, self.request_type)

                if not success:
                    logger.warning(f'Request failed, adding back to queue: {data}')
                    await self.queue.put((data, attempt + 1))
                else:
                    self.processed_queue.add(request_id)
                    logger.info(f'Request succeeded in the queue for {data}')
                    self.response_list.append(response_data)

                self.queue.task_done()
            except asyncio.CancelledError: 
                break
            except Exception as e:
                logger.error(f'Unexpected error in worker: {e}')
                await self.queue.put((data, attempt + 1))
    
# Starts off concurrent workers to work on the queue list
    async def process_queue(self):
        async with aiohttp.ClientSession() as session:
            for x in range(self.concurrency):
                task = asyncio.create_task(self.worker(session))
                self.worker_tasks.append(task)
            await self.queue.join()
            for task in self.worker_tasks:
                task.cancel()
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
            return len(self.processed_queue), self.response_list
