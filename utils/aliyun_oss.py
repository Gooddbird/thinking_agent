import os
import uuid

import oss2

from base.logger import logger

OSS_ACCESS_KEY_ID = os.getenv("OSS_ACCESS_KEY_ID")
OSS_ACCESS_KEY_SECRET = os.getenv("OSS_ACCESS_KEY_SECRET")
OSS_ENDPOINT = os.getenv("OSS_ENDPOINT")
OSS_BUCKET_NAME = os.getenv("OSS_BUCKET_NAME")

auth = oss2.Auth(OSS_ACCESS_KEY_ID, OSS_ACCESS_KEY_SECRET)
bucket = oss2.Bucket(auth, OSS_ENDPOINT, OSS_BUCKET_NAME)

class AliYunOSSUtil:

    @staticmethod
    def upload_file(file: str) -> str:
        try:
            filename = f"{uuid.uuid4().hex}{os.path.splitext(file)[1]}"
            bucket.put_object_from_file(filename, file)
            return bucket.sign_url("GET", filename, expires=3000)
        except Exception as e:
            logger.info(e)
            return "upload file failed: " + str(e)

if __name__ == "__main__":
    result = AliYunOSSUtil.upload_file(file="E:\\ai_workspace\\thinking_agent\\start\\1.txt")
    logger.info(result)