# Crossmint Challenge

## Features

- Build MegaVerse with instruction set parsed from goal_map
- Full MegaVerse deletion with more efficient instruction set (using the current map instead of the goal map, not specified in the API docs)
- Batch/Concurrent requests
- Double retry logic for extra safety
- Map validation
- Map mismatch detection (current map vs goal map)
- Map caching

## Instructions

- In main.py call the action function with the url, candidateId and either "clean" to delete the MegaVerse or "build" to build the MegaVerse.
- You can further change the parameters in the QueueProcessor the middle integer parameter defines the number of concurrent workers.
- You can also change the parameters in the Requests, the last two integers represent max_retries and delay_time respectively.
  (Changing the parameters is not necessary, current parameters work well, the only required parameter is clean and delete)

The project is broken down into three main components

- Requests
- QueueProcessor
- MapProcessor

### Requests:

- Get maps (It fetches current_map which is not mentioned in the docs and and goal_map)
- It creates POST requests for planets
- It creates DELETE requests for planets
- It takes in max_retry and delay_time parameters, to retry and wait if a request fails

### QueueProcessor:

- It takes in a payload (instructions for requests) and adds it into a queue.
- It creates workers based on defined concurrency parameter.
- Workers consume tasks from the queue and adds an extra layer of retry logic, by adding back into the queue if request fails after max_retries
  (technically it should add back into the queue until all requests return a status_code of 200, but 200 doesn't mean the request actually performed)

### MapProcessor:

- Gets maps and parses them into instructions ready for QueueProcessor's consumption.
- Validates current_map with goal_map using SHA-1 so it can just verify hashes.
- Returns mismatched elements if the hashes are not equal.


