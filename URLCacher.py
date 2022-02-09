'''
Created on Jan 11, 2022

@author: willg
'''

from collections import defaultdict
from datetime import datetime, timedelta
import aiohttp
import asyncio
import common

PRINT_REQUESTS = True
class URLCacher():
    """Class for asynchronous requests that caches the response"""

    def __init__(self, default_cache_seconds:int=45, allow_hanging:bool=True, hang_seconds:int=7, request_timeout:int=10):
        self._url_cache = defaultdict(URLCacher._default_cache_entry)
        self.default_cache_length = timedelta(seconds=default_cache_seconds)
        self.allow_hanging = allow_hanging
        self.hang_seconds = hang_seconds
        self.request_timeout = timedelta(seconds=request_timeout)
        self.maximum_cache_storage_length = self.default_cache_length + self.default_cache_length  # Maximum time that responses are stored are two times the cache length
        self._session = aiohttp.ClientSession()
        
    @staticmethod
    def _default_cache_entry():
        return {"currently_pulling": False,
                "time_sent": None,
                "time_received": None,
                "response_text": None}

    def _prepare_fetch(self, url: str):
        self._url_cache[url]["currently_pulling"] = True
        self._url_cache[url]["time_sent"] = datetime.now()

    def _finish_fetch(self, url: str, response_text: str):
        self._url_cache[url]["response_text"] = response_text
        self._url_cache[url]["time_received"] = datetime.now()
        self._url_cache[url]["currently_pulling"] = False
        
    async def _fetch_url(self, url: str) -> str:
        '''Sends an asychronous request for the given url, caches the response text, and returns the response text'''
        response_text = None
        self._prepare_fetch(url)
        try:
            timeout = aiohttp.ClientTimeout(total=float(self.request_timeout.total_seconds()))
            async with self._session.get(url, ssl=common.sslcontext, timeout=timeout) as response:
                response_text = await response.text()
        finally:
            self._finish_fetch(url, response_text)

        return response_text


    def is_url_expired(self, url: str, cache_length:timedelta=None, current_time:datetime=None) -> bool:
        '''Returns True if the given url response in the cache is expired, False is the cached reponse is still valid.
        If a response has never been cached, this function returns True'''
        cache_length = self.default_cache_length if cache_length is None else cache_length
        time_received = self._url_cache[url]["time_received"]
        if time_received is None:
            return True
        return self._is_expired_time(time_received, cache_length, current_time)

    def _is_expired_time(self, last_fetch_time: datetime, cache_length: timedelta, current_time:datetime=None) -> bool:
        current_time = datetime.now() if current_time is None else current_time
        return (current_time - last_fetch_time) > cache_length

    def _clean_old_cache(self):
        current_time = datetime.now()
        urls_to_delete = set()
        for url, url_data in self._url_cache.items():
            if url_data["currently_pulling"]:
                if self._is_expired_time(url_data["time_sent"], self.request_timeout):
                    urls_to_delete.add(url)
            elif self.is_url_expired(url, cache_length=self.maximum_cache_storage_length, current_time=current_time):
                urls_to_delete.add(url)
        
        for url in urls_to_delete:
            del self._url_cache[url]


    async def _can_hit_cache(self, url: str, cache_length: timedelta, allow_hanging: bool) -> bool:
        if self._url_cache[url]["currently_pulling"]:
            if allow_hanging:
                for _ in range(self.hang_seconds):
                    await asyncio.sleep(1)
                    if not self._url_cache[url]["currently_pulling"]:  # check if url is being pulled
                        break  # if it is, stop polling and break down to final return statement
                else:  # URL is still pulling, so we cannot hit the cache
                    return False

        return not self.is_url_expired(url, cache_length)


    async def get_url(self, url, cache_length:timedelta=None, allow_hanging:bool=None) -> str:
        '''Returns the text response for the specified url by either hitting the cache or sending an asynchronous request for the specified url
        If a request is sent, the response is stored in the cache
        
        To override using the default cache length for a url, specifiy a timedelta for cache_length
        
        Important: If the requested url has an outgoing request already that does not have a response yet, this function will hang until that response is returned, or a maximum number of seconds specified by self.hang_seconds
        If it hangs the maximum amount of time without the previous response finishing, an asynchronous request will be sent for the specified url.
        This behaviour is to minimize the requests sent for a URL if multiple requests for that URL all come in at the same time. If you do not wish for this behaviour to remain on, specify allow_hanging to be False
        I strongly encourage you to leave allow_hanging alone though, and instead lower the hanging number of seconds instead. (You're using a URLCaching class, why send 3 requests all at the same time when the first one will return a response and you can get that single response for all 3 requests?'''
        self._clean_old_cache()
        cache_length = self.default_cache_length if cache_length is None else cache_length
        allow_hanging = self.allow_hanging if allow_hanging is None else allow_hanging
        if await self._can_hit_cache(url, cache_length, allow_hanging):
            if PRINT_REQUESTS:
                cur_time = datetime.now()
                print(f"{cur_time.time()}: {url} hit the cache because page was downloaded {(cur_time - self._url_cache[url]['time_received']).total_seconds()} seconds ago.")
            return self._url_cache[url]["response_text"]
        else:
            if PRINT_REQUESTS:
                cur_time = datetime.now()
                print(f"{cur_time.time()}: {url} is making an HTTPS request.")
            return await self._fetch_url(url)