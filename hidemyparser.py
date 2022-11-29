import aiohttp
import anyio
import re

config = None # Your http(s) proxy. Unironically you need a proxy to parse a proxy webpage

class parser:

    def __init__(self):
        self.session = None

        self.output = open("proxies.txt", "a+", encoding='utf-8')

        self.main_url = "https://hidemy.name/en/proxy-list/"

        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'
        }

    async def send_request(self, method, url, **kwargs):
        try:
            async with self.session.request(method, url, proxy=config, **kwargs) as response:
                return await response.text()
        except Exception:
            return ""

    async def get_urls(self):
        n = 0
        urls = []

        response = await self.send_request("GET", self.main_url, headers=self.headers)
        if (indexes := sorted(re.findall("\/en\/proxy-list\/\?start=(\d+)#list", response))): #greatest index
            while n < int(indexes[0]):
                n += 64
                urls.append(f'{self.main_url}?start={n}')
            return urls
        return []

    async def fetch_proxies(self, url, semaphore):
        while not (response := await self.send_request("GET", url, headers=self.headers)):
            await anyio.sleep(1)

        semaphore.release()
            
        if (proxies := re.findall("<td>([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})<\/td><td>(\d+)<", response)):
            proxy_list = "\n".join("{}:{}".format(*proxy) for proxy in proxies)
            self.output.write(f'{proxy_list}\n')

            print(f"Fetched {len(proxies)} proxies from {url}")
            
        else:
            print(f"Couldn't fetch any proxies from {url}.")

    async def main(self):
        self.session = aiohttp.ClientSession()
        semaphore = anyio.Semaphore(25)

        urls = await self.get_urls()
        if urls:
            async with anyio.create_task_group() as group:
                for url in urls:
                    await semaphore.acquire()
                    group.start_soon(self.fetch_proxies, url, semaphore)

        else:
            print("Failed to parse HideMyName indexes, please try again.")

        print("Done!")

        self.output.close()
        await self.session.close()

if __name__ == "__main__":
    anyio.run(parser().main)
