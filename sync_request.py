import logging
from typing import Optional, Tuple, Union
import requests
from telegram.request import BaseRequest
from telegram.request._baserequest import DefaultValue, RequestData

logger = logging.getLogger(__name__)

class SyncRequest(BaseRequest):
    """Синхронный запрос через библиотеку requests"""
    
    def __init__(
        self,
        connect_timeout: float = 5.0,
        read_timeout: float = 5.0,
        write_timeout: float = 5.0,
        pool_timeout: float = 1.0,
    ):
        self._connect_timeout = connect_timeout
        self._read_timeout = read_timeout
        self._write_timeout = write_timeout
        self._pool_timeout = pool_timeout
    
    @property
    def read_timeout(self) -> float:
        return self._read_timeout
    
    @property
    def write_timeout(self) -> float:
        return self._write_timeout
    
    @property
    def connect_timeout(self) -> float:
        return self._connect_timeout
    
    @property
    def pool_timeout(self) -> float:
        return self._pool_timeout
    
    async def initialize(self) -> None:
        logger.debug("SyncRequest initialized")
    
    async def shutdown(self) -> None:
        logger.debug("SyncRequest shutdown")
    
    async def do_request(
        self,
        method: str,
        url: str,
        headers: Optional[dict] = None,
        data: Optional[bytes] = None,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Tuple[int, bytes]:
        """Выполняет HTTP запрос синхронно"""
        
        logger.info(f"SyncRequest: {method} {url}")
        
        # Извлекаем request_data
        request_data = kwargs.get('request_data')
        
        # Преобразуем RequestData в bytes
        if isinstance(request_data, RequestData):
            # RequestData имеет метод json_bytes или параметры
            if hasattr(request_data, 'json_bytes'):
                data = request_data.json_bytes
            elif hasattr(request_data, 'parameters'):
                import json
                data = json.dumps(request_data.parameters).encode('utf-8')
            elif hasattr(request_data, 'multipart_data'):
                data = request_data.multipart_data
            else:
                # Пробуем преобразовать в JSON
                import json
                data = json.dumps(request_data.__dict__).encode('utf-8')
        elif request_data is not None:
            data = request_data
        elif data is None:
            data = b''
        
        # Извлекаем таймауты
        connect_timeout = kwargs.get('connect_timeout', self._connect_timeout)
        read_timeout = kwargs.get('read_timeout', self._read_timeout)
        write_timeout = kwargs.get('write_timeout', self._write_timeout)
        
        # Заменяем DefaultValue
        if isinstance(connect_timeout, DefaultValue):
            connect_timeout = self._connect_timeout
        if isinstance(read_timeout, DefaultValue):
            read_timeout = self._read_timeout
        if isinstance(write_timeout, DefaultValue):
            write_timeout = self._write_timeout
        
        # Формируем таймаут
        if timeout is None:
            timeout = connect_timeout + read_timeout + write_timeout
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                data=data,
                timeout=timeout,
            )
            
            logger.info(f"SyncRequest response: {response.status_code}")
            return response.status_code, response.content
            
        except Exception as e:
            logger.error(f"SyncRequest error: {e}")
            raise