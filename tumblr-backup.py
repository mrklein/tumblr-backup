#!/usr/bin/env python

# The MIT License (MIT)

# Copyright (c) 2013 Alexey Matveichev

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import argparse
import os
import sys
from threading import Thread
from Queue import Queue
from time import sleep
from functools import partial
from datetime import datetime
from json import loads
from urllib2 import urlopen
from urlparse import urlparse


__version__ = '0.0.1'


NTHREADS = 10
DEFAULT_LIMIT = 20
DOWNLOADER_DELAY = 2
EXIT_DELAY = 5


def init_object(obj, fields, data):
    for f in fields:
        if f in data:
            setattr(obj, '_%s' % f, data[f])
        else:
            setattr(obj, '_%s' % f, None)


class Post(object):
    def __init__(self, data):
        fields = ['id', 'post_url', 'type', 'timestamp', 'date', 'format',
                  'tags']
        init_object(self, fields, data)

    def _get_slug(self):
        sl_idx = self._post_url.rfind('/')
        return self._post_url[sl_idx + 1:]

    def save(self, path):
        raise NotImplemented('')


class Text(Post):
    def __init__(self, data):
        fields = ['title', 'body']
        init_object(self, fields, data)
        super(Text, self).__init__(data)

    def save(self, path):
        pass


class Quote(Post):
    def __init__(self, data):
        fields = ['text', 'source']
        init_object(self, fields, data)
        super(Quote, self).__init__(data)

    def save(self, path):
        pass


class Photo(Post):
    def __init__(self, data):
        fields = ['photos', 'caption', 'width', 'height']
        init_object(self, fields, data)
        super(Photo, self).__init__(data)

    def _get_format(self, url):
        return os.path.splitext(url)[1]

    def save(self, path):
        res = []
        i_cnt = 0
        for p in self._photos:
            url = p['original_size']['url']
            filename = '%d-%s-%d%s' % (self._id, self._get_slug(), i_cnt,
                                       self._get_format(url))
            save_path = os.path.join(path, 'photo', filename)
            i_cnt += 1
            res.append((url, save_path))

        return res


class Link(Post):
    def __init__(self, data):
        fields = ['title', 'url', 'description']
        init_object(self, fields, data)
        super(Link, self).__init__(data)

    def save(self, path):
        pass


class ChatItem(object):
    def __init__(self, name='', label='', phrase=''):
        self._name = name
        self._label = label
        self._phrase = phrase

    def __str__(self):
        return ''


class Chat(Post):
    def __init__(self, data):
        fields = ['title', 'body', 'dialogue']
        init_object(self, fields, data)
        super(Chat, self).__init__(data)

    def save(self, path):
        pass


class Audio(Post):
    def __init__(self, data):
        fields = ['caption', 'player', 'plays', 'album_art', 'artist', 'album',
                  'track_name', 'track_number', 'year']
        init_object(self, fields, data)
        super(Audio, self).__init__(data)

    def save(self, path):
        pass


class Video(Post):
    def __init__(self, data):
        fields = ['caption', 'player']
        init_object(self, fields, data)
        super(Video, self).__init__(data)

    def save(self, path):
        pass


class Answer(Post):
    def __init__(self, data):
        fields = ['asking_name', 'asking_url', 'question', 'answer']
        init_object(self, fields, data)
        super(Answer, self).__init__(data)

    def save(self, path):
        pass


class Tumblr(object):
    base_url = 'http://api.tumblr.com/v2/blog'
    # Shamelessly taken from https://github.com/Fugiman/Tumblr-Backup
    api_key = 'RfTll0TPYGVm3kTbauZRH5QVAgBH3UAkQcpPmHDIMaWEa9xtY8'

    def __init__(self, url, api_key):
        self._url = url
        self._netloc = url
        self._posts = 0
        self._title = ''
        self._updated_on = datetime.now()
        self._description = ''
        self._ask = False
        self._ask_anon = False
        self._likes = 0
        self._share_likes = False
        self._is_nsfw = False
        self._api_key = api_key

        self.__update()

    def __update(self):
        call_url = "%s/%s/info?api_key=%s" % (Tumblr.base_url,
                                              self._netloc,
                                              Tumblr.api_key)
        f = urlopen(call_url)
        t = loads(f.read())

        for k, v in t['response']['blog'].items():
            setattr(self, '_%s' % k, v)

        o = urlparse(self._url)
        self._netloc = o.netloc

    @property
    def posts(self):
        return self._posts

    @property
    def likes(self):
        return self._likes

    def avatar(self, size=64):
        call_url = '%s/%s/avatar/%d' % (Tumblr.base_url, self._netloc, size)
        f = urlopen(call_url)
        t = loads(f.read())

        return t['response']['avatar_url']

    def get_posts(self, offset=0, nitems=20):
        call_url = '%s/%s/posts?api_key=%s' % (Tumblr.base_url,
                                               self._netloc,
                                               Tumblr.api_key)
        if offset > 0:
            call_url += "&offset=%d" % offset

        f = urlopen(call_url)
        t = loads(f.read())
        f.close()

        return t['response']['posts']

    def get_likes(self, offset=0, nitems=20):
        call_url = '%s/%s/likes?api_key=%s' % (Tumblr.base_url,
                                               self._netloc,
                                               Tumblr.api_key)
        if offset > 0:
            call_url += '&offset=%d' % offset

        f = urlopen(call_url)
        t = loads(f.read())

        return t['response']['liked_posts']


def downloader(queue, target, delay, **kwargs):
    """Reads URL from queue and download file from that URL"""
    while True:
        try:
            url, path = queue.get()
            f1 = open(path, 'w')
            f2 = urlopen(url)
            f1.write(f2.read())
            f1.close()
            f2.close()
            sleep(delay)
        except:
            print("Failed URL: %s" % url)
        queue.task_done()


def save_posts(posts, path, queue):
    for post in posts:
        p = constructors[post['type']](post)
        if not p._type in ['photo']:
            p.save(path)
        else:
            ts = p.save(path)
            if type(ts) == tuple:
                queue.put(ts)
            else:
                for itm in ts:
                    queue.put(itm)


constructors = {
    'text': Text,
    'quote': Quote,
    'photo': Photo,
    'link': Link,
    'chat': Chat,
    'audio': Audio,
    'video': Video,
    'answer': Answer
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Backup Tumblr blog')
    parser.add_argument('hostname', type=str, help='Blog host name')
    parser.add_argument('-l', '--likes', help='Also backup likes',
                        action="store_true")
    parser.add_argument('-d', '--destination',
                        help='Destination directory for the backup',
                        type=str, default='.')

    args = parser.parse_args()

    tumblr = Tumblr(args.hostname, Tumblr.api_key)

    if args.destination != '.' and not os.path.exists(args.destination):
        posts_path = os.path.join(args.destination, 'posts')

    if args.destination == '.':
        posts_path = os.path.join('posts')

    if not os.path.exists(posts_path):
        os.makedirs(posts_path)

    post_types = ['text', 'photo', 'quote', 'link', 'chat', 'audio', 'video',
                  'answer']
    for t in post_types:
        tp = os.path.join(posts_path, t)
        if not os.path.exists(tp):
            os.makedirs(tp)

    queue = Queue()

    for i in xrange(NTHREADS):
        t = Thread(target=partial(downloader, queue, '.', DOWNLOADER_DELAY))
        t.daemon = True
        t.start()

    print('Staring backup.')
    print('Backing up posts...')
    for offset in xrange(0, tumblr.posts, DEFAULT_LIMIT):
        save_posts(tumblr.get_posts(offset=offset), posts_path, queue)
        sys.stdout.write('%d...' % offset)
        sys.stdout.flush()
    print('Done.')

    if args.likes:
        likes_path = os.path.join(args.destination, 'likes')
        if not os.path.exists(likes_path):
            os.makedirs(likes_path)
            for t in post_types:
                tp = os.path.join(likes_path, t)
                if not os.path.exists(tp):
                    os.makedirs(tp)

        print('Backing up likes...')
        for offset in xrange(0, tumblr.likes, DEFAULT_LIMIT):
            save_posts(tumblr.get_likes(offset=offset), likes_path, queue)
            sys.stdout.write('%d...' % offset)
            sys.stdout.flush()
        print('Done.')

    while True:
        qs = queue.qsize()
        print('URLs in queue: %d' % qs)
        sleep(EXIT_DELAY)
        if qs == 0:
            break
