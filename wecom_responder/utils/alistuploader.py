import loguru
import requests
import os
import urllib.parse
import pydantic
from wecom_responder.utils.config import config_manager

class AlistPutFormResp(pydantic.BaseModel):
    code: int
    message: str
    data: dict = None

class AlistUploader:
    def __init__(self):
        # 从 config.json 读取 nspshare_chan 的配置
        conf = config_manager.get_param('nspshare_chan')
        try:
            self.api_url = conf['alist']['api_url']
            self.token = conf['alist']['token']
        except KeyError as e:
            raise ValueError(f"配置缺失: {e}")

    def upload_file(self, file_path, remote_path):
        """
        上传文件到 Alist
        :param file_path: 本地文件路径
        :param remote_path: 远程文件路径（完整路径）
        """
        try:
            file_size = os.path.getsize(file_path)
            headers = {
                "Authorization": self.token,
                "Content-Length": str(file_size),
                "File-Path": urllib.parse.quote(remote_path),
                "Overwrite": 'true',
            }
            with open(file_path, "rb") as file:
                files = {"file": file}
                response = requests.put(f"{self.api_url}/api/fs/form", headers=headers, files=files)
            if response.status_code == 200:
                data = response.json()
                resp = AlistPutFormResp.model_validate(data)
                return resp.code, resp.message
            else:
                loguru.logger.error(f"文件上传失败，状态码: {response.status_code}")
                loguru.logger.error(response.text)
                return response.status_code, f"文件上传失败: {response.text}"
        except Exception as e:
            loguru.logger.error(f"上传文件时发生错误: {e}")
            return -1, f"上传文件时发生错误: {e}"

alist_uploader = AlistUploader()

# 示例用法
if __name__ == "__main__":
    uploader = AlistUploader()
    uploader.upload_file("/root/test.conf", "/nspshare/temp/test.conf")