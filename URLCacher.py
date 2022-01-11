'''
Created on Jan 11, 2022

@author: willg
'''

from collections import defaultdict
from datetime import datetime, timedelta
import aiohttp
import asyncio
import common

class URLCacher():
    """Class for asynchronous requests that caches the response"""

    def __init__(self, default_cache_length=timedelta(seconds=45), allow_hanging=True, hang_seconds=7):
        self.url_cache = defaultdict(URLCacher.__default_cache_entry__)
        self.default_cache_length = default_cache_length
        self.allow_hanging = allow_hanging
        self.hang_seconds = hang_seconds
        self.session = aiohttp.ClientSession()
        self.cache_pulling_timeout = timedelta(seconds=10)
        self.maximum_cache_storage_length = default_cache_length + default_cache_length #Maximum time that responses are stored are two times the cache length

    @staticmethod
    def __default_cache_entry__():
        return {"currently_pulling":False,
                "time_sent":None,
                "time_received":None,
                "response_text":None}

    def __prepare_fetch__(self, url):
        self.url_cache[url]["currently_pulling"] = True
        self.url_cache[url]["time_sent"] = datetime.now()

    def __finish_fetch__(self, url, response_text):
        self.url_cache[url]["response_text"] = response_text
        self.url_cache[url]["time_received"] = datetime.now()
        self.url_cache[url]["currently_pulling"] = False
        
    async def __fetch_url__(self, url):
        '''Sends an asychronous request for the given url, caches the response text, and returns the response text'''
        response_text = None
        self.__prepare_fetch__(url)
        try:
            async with self.session.get(url, ssl=common.sslcontext) as response:
                response_text = await response.text()
        finally:
            self.__finish_fetch__(url, response_text)

        return response_text


    def is_url_expired(self, url, cache_length:timedelta=None, current_time=None):
        '''Returns True if the given url response in the cache is expired, False is the cached reponse is still valid.
        If a response has never been cached, this function returns True'''
        cache_length = self.default_cache_length if cache_length is None else cache_length
        time_received = self.url_cache[url]["time_received"]
        if time_received is None:
            return True
        return self.__is_expired_time__(time_received, cache_length, current_time)

    def __is_expired_time__(self, last_fetch_time, cache_length, current_time=None):
        current_time = datetime.now() if current_time is None else current_time
        return (current_time - last_fetch_time) > cache_length

    def __clean_old_cache__(self):
        current_time = datetime.now()
        urls_to_delete = set()
        for url, url_data in self.url_cache.items():
            if url_data["currently_pulling"]:
                if self.__is_expired_time__(url_data["time_sent"], self.cache_pulling_timeout):
                    urls_to_delete.add(url)
            elif self.is_url_expired(url, cache_length=self.maximum_cache_storage_length, current_time=current_time):
                urls_to_delete.add(url)
        
        for url in urls_to_delete:
            del self.urls_to_delete[url]


    async def __can_hit_cache__(self, url, cache_length, allow_hanging):
        if self.url_cache[url]["currently_pulling"]:
            if allow_hanging:
                for _ in range(self.hang_seconds):
                    await asyncio.sleep(1)
                    if not self.url_cache[url]["currently_pulling"]: #check if url is being pulled
                        break #if it is, stop polling and break down to final return statement
                else: #URL is still pulling, so we cannot hit the cache
                    return False

        return not self.is_url_expired(url, cache_length)


    async def get_url(self, url, cache_length:timedelta=None, allow_hanging:bool=None):
        '''Returns the text response for the specified url by either hitting the cache or sending an asynchronous request for the specified url
        If a request is sent, the response is stored in the cache
        
        To override using the default cache length for a url, specifiy a timedelta for cache_length
        
        Important: If the requested url has an outgoing request already that does not have a response yet, this function will hang until that response is returned, or a maximum number of seconds specified by self.hang_seconds
        If it hangs the maximum amount of time without the previous response finishing, an asynchronous request will be sent for the specified url.
        This behaviour is to minimize the requests sent for a URL if multiple requests for that URL all come in at the same time. If you do not wish for this behaviour to remain on, specify allow_hanging to be False
        I strongly encourage you to leave allow_hanging alone though, and instead lower the hanging number of seconds instead. (You're using a URLCaching class, why send 3 requests all at the same time when the first one will return a response and you can get that single response for all 3 requests?'''
        self.__clean_old_cache__()
        cache_length = self.default_cache_length if cache_length is None else cache_length
        allow_hanging = self.allow_hanging if allow_hanging is None else allow_hanging
        if self.__can_hit_cache__(url, cache_length, allow_hanging):
            return self.url_cache[url]["response_text"]
        else:
            return await self.__fetch_url__(url)