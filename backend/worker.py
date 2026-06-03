import json
import logging
import sys
import time

import redis as redis_lib

from db.redis import get_client, set_job_status
from services.ingest import process_file_job

logging.basicConfig(level=logging.INFO, format="%(asctime)s [worker] %(message)s")
logger = logging.getLogger(__name__)

QUEUE_KEY = "ingest_queue"


def run_worker() -> None:
    logger.info("Worker iniciado, aguardando jobs...")
    while True:
        try:
            r = get_client()
            _, raw = r.blpop(QUEUE_KEY)
            job: dict = json.loads(raw)
            job_id = job["job_id"]
            filename = job.get("filename", "")
            user_id = job.get("user_id", "")

            set_job_status(job_id, "processing", filename=filename, user_id=user_id)
            logger.info(f"Processando job {job_id}: {filename}")

            try:
                process_file_job(job)
                set_job_status(job_id, "done", filename=filename, namespace=job.get("namespace"), user_id=user_id)
                logger.info(f"Job {job_id} concluído")
            except Exception as e:
                set_job_status(job_id, "error", filename=filename, error=str(e), user_id=user_id)
                logger.error(f"Job {job_id} falhou: {e}")

        except (redis_lib.exceptions.TimeoutError, redis_lib.exceptions.ConnectionError) as e:
            logger.warning(f"Conexão Redis perdida, reconectando em 2s: {e}")
            time.sleep(2)


if __name__ == "__main__":
    try:
        run_worker()
    except KeyboardInterrupt:
        logger.info("Worker encerrado")
        sys.exit(0)
