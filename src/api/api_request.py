import aiohttp
import asyncio
import logging
import requests
import os
import json

logger = logging.getLogger(__name__)

class Requests:
    def __init__(self, url, candidate_id, max_retries, retry_delay):
        self.url = url
        self.candidate_id = candidate_id
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    # Get either the goal map or the current map( current_map is useful for deletions, reduces the api calls and good for validation)    
    def get_map(self, file_name, type_map, store):
        if(type_map == "current_map"):
            url = f'{self.url}/map/{self.candidate_id}'
        elif(type_map == "goal_map"):
            url = f'{self.url}/map/{self.candidate_id}/goal'
        if(store == "server"):
            try:
                response = requests.get(url)
                response.raise_for_status()
                data = response.json()

                with open(f'maps/{file_name}', 'w') as json_file:
                    json.dump(data, json_file, indent=4)
                if(type_map == "current_map"):
                    return data["map"]["content"]
                else:
                    return data["goal"]
                logger.info("Map has been saved as a JSON file in the maps directory")
            except requests.exceptions.RequestException as e:
                logger.info(f'Error: {e}')
                return None
        elif(store == "disk"):
            if(os.path.isfile(f'maps/{file_name}')):
                logger.info("This map has already been downloaded")
                with open(f'maps/{file_name}', 'r') as challenge_map:
                    if(current):
                        return json.load(challenge_map)["map"]["content"]
                    else:
                        return json.load(challenge_map)["goal"]
            else:
                try:
                    response = requests.get(url)
                    response.raise_for_status()
                    data = response.json()

                    with open(f'maps/{file_name}', 'w') as json_file:
                        json.dump(data, json_file, indent=4)
                    if(current):
                        return data["map"]["content"]
                    else:
                        return data["goal"]
                    logger.info("Map has been saved as a JSON file in the maps directory")
                except requests.exceptions.RequestException as e:
                    logger.info(f'Error: {e}')
                    return None

    # General POST request for any of the 3 planets, attempt keeps track in case of failure
    async def planet_request(self, session, data, attempt, request_type):
        if data["name"] == "space":
            return True
        url = f'{self.url}/{data["name"]}s'
        try:
            if(request_type == "POST"):
                request = session.post(url, json=data["data"])
            elif(request_type == "DELETE"):
                request = session.delete(url, json=data["data"])
            else:
                logger.error(f'Request type: {request_type} does not exist')

            async with request as response:
                response_data = {
                    'status': response.status,
                    'text': await response.text(),
                    'headers': dict(response.headers)
                }
                if response.status == 200:
                    logger.info(f'Request succeeded for {data}')
                    await asyncio.sleep(self.retry_delay)
                    return True, response_data
                else: 
                    if attempt < self.max_retries:
                        delay = self.retry_delay * (2 ** (attempt - 1))
                        logger.info(f'Retrying after {delay} seconds...')
                        await asyncio.sleep(delay)
                        return await self.planet_request(session, data, attempt + 1, request_type)
                    else:
                        return False, response_data
        except Exception as e:
            logger.warning(f'Request failed, attempt {attempt}: {e}')
            error_data = {
                'error': str(e),
            }
            if attempt < self.max_retries:
                delay = self.retry_delay * (2 ** (attempt - 1))
                logger.info(f'Retrying after {delay} seconds...')
                await asyncio.sleep(delay)
                return await self.planet_request(session, data, attempt + 1, request_type)
            logger.error(f'Request failed after max attempts: {data}')
            return False, error_data




