import requests
import json
import os
import time
from api.api_request import Requests
from processor.map_processor import MapProcessor
from processor.queue_processor import QueueProcessor
import logging
import asyncio

# logging config 
logging.basicConfig(
    level=logging.INFO,  
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def action(candidate_id, url, action_type):
    result = False
    if(action_type == "clean"):
        request_payload_type = "delete"
        queue_operation_type = "DELETE"
        validation_type = "empty"
    elif(action_type == "build"):
         request_payload_type = "create"
         queue_operation_type = "POST"
         validation_type = "goal"
    # Requests takes in a url and a candidate_id, max_retries and delay_time and it builds and sends requests
    # It can get maps as well as post and delete planets.
    request_instance = Requests(url, candidate_id, 5, 1)
    # QueueProcessor takes in a Requests Object, a concurrency, and a operation "POST" or "DELETE"
    # This is done to configure how many workers you want to concurrently POST or DELETE planets.
    # The current API has a very low rate limit so it is advisable to use max 2 workers. 
    queue_processor = QueueProcessor(request_instance, 5, queue_operation_type)
    # We create a second QueueProcessor to use it as a last resort once we fail to validate our current_map with the goal_map
    # We set it to 1 worker, to reduce the chances of silently failing to POST a planet
    retry_queue_processor = QueueProcessor(request_instance, 1, queue_operation_type)
    # MapProcessor takes in a Requests Object and it is in charge of making the requests to get the current and goal maps
    # It will then process the maps into instructions that can be fed directly into the QueueProcessor. The MapProcessor can also
    # help to validate maps, checking the current_map against the goal_map and returning the difference
    map_processor = MapProcessor(request_instance)

    payload = map_processor.get_request_payload(request_payload_type) 
    
    await queue_processor.add_to_queue(payload)
    await queue_processor.process_queue()

    # Validating current_map and goal_map after running the QueueProcessor once
    result, mismatched_entries = map_processor.validate_map(validation_type)
    if(result):
        logger.info(f'The SHA-1 hash of current_map matches the hash of {validation_type}_map')
        logger.info(f'{action_type.upper()} process completed')
    else:
        logger.info(f'The SHA-1 hash of current_map does not match the hash of goal_map')
        logger.info(f'Retrying with one worker')
        payload = map_processor.get_request_payload("retry")
        print(payload)
        await retry_queue_processor.add_to_queue(payload)
        res, data = await retry_queue_processor.process_queue()
        logger.info(f'After Retry, we processed {res} requests')
        logger.info("Done retrying")
        final_result, _ = map_processor.validate_map(validation_type)
        logger.warning(f'current_map == goal_map is {final_result}')

if __name__ == "__main__":
    candidate_id = "1bc80e14-c5ec-4be1-8da7-08ed2eb1ca10"
    url = "https://challenge.crossmint.io/api"

    asyncio.run(action(candidate_id, url, "build"))        
 
