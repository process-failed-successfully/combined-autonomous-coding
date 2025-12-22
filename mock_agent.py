import os
import time
import redis
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

redis_host = os.environ.get("REDIS_HOST", "redis-master")
queue_name = os.environ.get("REDIS_QUEUE", "jira_ticket_queue")

try:
    r = redis.Redis(host=redis_host, port=6379, db=0)
    logger.info(f"Mock Agent started. Monitoring queue: {queue_name} on {redis_host}")
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    exit(1)

while True:
    try:
        ticket = r.lpop(queue_name)
        if ticket:
            ticket_id = ticket.decode('utf-8')
            logger.info(f"Processing ticket: {ticket_id}")
            time.sleep(5)
            logger.info(f"Finished ticket: {ticket_id}")
        else:
            time.sleep(2)
    except Exception as e:
        logger.error(f"Error in work loop: {e}")
        time.sleep(5)
