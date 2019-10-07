def check_env():
    try:
        import requests
        import efficiency
        import tqdm
        import lxml
    except ImportError:
        import os
        os.system('pip install efficiency requests tqdm lxml')
        os.system('pip3 install efficiency requests tqdm lxml')


class HackerNewsPage:
    INVALID_HTML = '[INVALID_HTML]'

    def __init__(self, date, page=1):
        self.date = date
        self.page = page
        self.base_url = 'https://news.ycombinator.com/'
        self.stories = []

    def set_url(self, next_page=False):
        if next_page: self.page += 1
        self.url = '{base_url}front?day={day}&p={page}' \
            .format(base_url=self.base_url, day=self.date, page=self.page)
        return self.url

    def set_html(self, use_proxy=False):
        import time
        import requests
        from efficiency.log import show_time

        sleeper.sleep()
        headers = {'User-Agent': next(user_agents)}

        if use_proxy:
            proxy = next(proxy_pool)

            try:
                r = requests.get(self.url,
                                 proxies={"http": proxy, "https": proxy},
                                 headers=headers)
            except Exception:
                proxy_pool.add_bad_proxy(proxy)
                self.set_html(use_proxy=use_proxy)
                return
        else:
            try:
                r = requests.get(self.url, headers=headers)
            except:
                sleeper.warn()
                storage.save_json()

                sleeper.hibernate(self.url)
                r = requests.get(self.url, headers=headers)

        if r.status_code == 403:
            sleeper.warn()
            storage.save_json()
            sleeper.hibernate(self.url)
            self.set_html(use_proxy=use_proxy)

        elif r.status_code == 404:
            return self.INVALID_HTML
        elif r.status_code == 200:
            self.html = r.text
            return self.html

    def parse_html(self):
        from lxml.html import fromstring
        from lxml import etree
        from efficiency.log import show_var

        tree = fromstring(self.html)

        athing_elems = tree.xpath('//a[@class="storylink"]')
        subtext_elems = tree.xpath('//span[@class="score"]')

        for athing, subtext in zip(athing_elems, subtext_elems):
            title = athing.text
            url_news = athing.attrib['href']
            site = athing.getnext()
            if site is not None:
                site = site.xpath('.//span[@class="sitestr"]/text()')[0]

            vote_num = subtext.text
            user = subtext.getnext().text
            comment = subtext.getnext().getnext().getnext().getnext().getnext()
            if comment is not None:
                comment_num = comment.text.replace('\xa0', ' ')
                url_comments = comment.attrib['href']
            else:
                comment_num = None
                url_comments = None

            self.stories.append({
                "title": title,
                "date": self.date,
                "vote_num": vote_num,
                "comment_num": comment_num,
                "user": user,
                "site": site,
                "url_news": url_news,
                "url_comments": url_comments,
            })

            # etree.tostring(comment)

        more_link = tree.xpath('//a[@class="morelink"]')

        return bool(more_link)

    def recursively_crawl(self):
        next_page = False
        for _ in range(100):
            self.set_url(next_page=next_page)
            html = self.set_html()
            if html == self.INVALID_HTML: break
            next_page = self.parse_html()
            if not next_page: break

        return self.stories


class HackerNewsData:

    def __init__(self, start_date='20190101', end_date='20190104'):
        self.date_range = self.get_date_range(start_date, end_date)

    def crawl_data(self):
        for date in self.date_range:
            webpage = HackerNewsPage(date, page=1)
            stories = webpage.recursively_crawl()
            print('[Info] {}, {}pages, {}stories'.format(date, webpage.page,
                                                         len(stories)))
            storage.add_data(stories)
            storage.save_json()
        import pdb;
        pdb.set_trace()

    @staticmethod
    def get_date_range(start_date, end_date):
        import datetime
        start_date = datetime.datetime.strptime(start_date, '%Y%m%d')
        end_date = datetime.datetime.strptime(end_date, '%Y%m%d')

        def daterange(start_date, end_date):
            for n in range(int((end_date - start_date).days)):
                yield start_date + datetime.timedelta(n)

        date_range = []
        for single_date in daterange(start_date, end_date):
            date_range.append(single_date.strftime("%Y-%m-%d"))
        return date_range


class Storage:
    def __init__(self, file='stories_2019.json'):
        import os
        import json

        self.data = []
        self.file = file
        if os.path.isfile(file):
            with open(file) as f:
                self.data = json.load(f)

    def add_data(self, new_data):
        storage.data.extend(new_data)

    def save_json(self):
        import json
        from efficiency.log import fwrite

        fwrite(json.dumps(self.data, indent=4), self.file)


class Sleeper:
    def __init__(self, block_secs=60 * 60, hour_max=30):
        self.url = ''
        self.block_times = 1
        self.block_secs = block_secs
        self.interval = int(60 * 60 / hour_max)

        self.init = True

    def sleep(self):
        if self.init:
            self.init = False
            return

        import time
        time.sleep(self.interval)

    def hibernate(self, url):
        import time

        if self.init:
            return

        if self.url == url:
            self.block_times += 1
        else:
            self.url = url
            self.block_times = 1
        time.sleep(self.block_secs * self.block_times)
        self.block_secs *= 1.5

    def warn(self):
        from efficiency.log import show_time
        show_time('[Warn] {} is blocked for {}s'
                  .format(self.url, sleeper.block_secs))


class ProxyPool:
    def __init__(self, proxy_file=''):
        from itertools import cycle
        from time import time

        proxies = self.get_proxies(proxy_file)
        self.proxies = self.verify_proxies(proxies)
        self.proxy_pool = cycle(self.proxies)
        self.bad_proxy_cnt = {}
        self.bad_proxy_cnt_limit = 5
        self.start_time = time()
        self.time_limit = 60 * 30

    def __next__(self):
        from time import time

        if (time() - self.start_time > self.time_limit) or len(
                self.proxies) < 5:
            self.__init__()
        return next(self.proxy_pool)

    def __len__(self):
        return len(self.proxies)

    def add_bad_proxy(self, proxy):
        from itertools import cycle

        if proxy not in self.bad_proxy_cnt:
            self.bad_proxy_cnt[proxy] = 1
        else:
            self.bad_proxy_cnt[proxy] += 1
            if self.bad_proxy_cnt[proxy] > self.bad_proxy_cnt_limit:
                self.proxies -= {proxy}
                self.proxy_pool = cycle(self.proxies)

    @staticmethod
    def get_proxies(proxy_file=''):
        if proxy_file:
            with open(proxy_file) as f:
                proxies = [line.strip() for line in f if line.strip()]
            return proxies

        import requests
        from lxml.html import fromstring

        url = 'https://free-proxy-list.net/'
        response = requests.get(url)
        parser = fromstring(response.text)
        proxies = []
        for i in parser.xpath('//tbody/tr'):
            if i.xpath('.//td[7][contains(text(),"yes")]'):
                # Grabbing IP and corresponding PORT
                proxy = ":".join([i.xpath('.//td[1]/text()')[0],
                                  i.xpath('.//td[2]/text()')[0]])
                proxies.append(proxy)
        return proxies

    @staticmethod
    def verify_proxies(proxies):
        import requests
        from tqdm import tqdm

        print('[Info] Checking proxies:', proxies)

        url = 'https://free-proxy-list.net/'
        valid_proxies = set()
        for proxy in tqdm(proxies):
            try:
                r = requests.get(url, proxies={"http": proxy, "https": proxy})
                valid_proxies |= {proxy}
                if len(valid_proxies) > 10:
                    break
            except Exception:
                pass
        if not valid_proxies:
            print('[Info] No valid proxies. Exiting program...')
            import sys
            sys.exit()

        print('[Info] Using proxies:', valid_proxies)

        return valid_proxies


if __name__ == '__main__':
    import argparse
    from itertools import cycle

    parser = argparse.ArgumentParser('Python Crawler for Hacker News')
    parser.add_argument('-start_date', default='20190101', type=str,
                        help='date to start crawling from')
    parser.add_argument('-end_date', default='20191008', type=str,
                        help='date to start crawling from')

    parser.add_argument('-hour_max', default=40, type=int,
                        help='number of websites to crawl every hour')
    parser.add_argument('-use_proxy', action='store_true',
                        help='whether to use free proxies online')
    parser.add_argument('-proxy_file', default='data/proxy00.txt',
                        help='path to file which stores a list of proxies')
    args = parser.parse_args()

    check_env()

    if args.use_proxy:
        import signal


        def handler(signum, frame): raise Exception("end of time")


        signal.signal(signal.SIGALRM, handler)

        proxy_pool = ProxyPool(args.proxy_file)
        args.hour_max *= len(proxy_pool)

    sleeper = Sleeper(hour_max=args.hour_max)

    user_agents = cycle([
        "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; AcooBrowser; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
        "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0; Acoo Browser; SLCC1; .NET CLR 2.0.50727; Media Center PC 5.0; .NET CLR 3.0.04506)",
        "Mozilla/4.0 (compatible; MSIE 7.0; AOL 9.5; AOLBuild 4337.35; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
        "Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)",
        "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)",
        "Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 6.0; Trident/4.0; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 1.0.3705; .NET CLR 1.1.4322)",
        "Mozilla/4.0 (compatible; MSIE 7.0b; Windows NT 5.2; .NET CLR 1.1.4322; .NET CLR 2.0.50727; InfoPath.2; .NET CLR 3.0.04506.30)",
    ])

    storage = Storage()
    hn_data = HackerNewsData(start_date=args.start_date, end_date=args.end_date)
    stories = hn_data.crawl_data()
