#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tootin' bot, but with supervision
"""

from airtight.cli import configure_commandline
from bs4 import BeautifulSoup
import getpass
import json
import logging
from mastodon import Mastodon
from pleiades.mastodon.brain import Brain
from pleiades.walker.walker import PleiadesWalker
from pprint import pformat
from os.path import abspath, join, realpath
import random
import shutil
import sys
from textwrap import TextWrapper
from time import sleep

DEFAULT_LOG_LEVEL = logging.WARNING
OPTIONAL_ARGUMENTS = [
    # each row is a list with 5 elements: short option, long option,
    # default value, help text, required
    ['-l', '--loglevel', 'NOTSET',
        'desired logging level (' +
        'case-insensitive string: DEBUG, INFO, WARNING, or ERROR',
        False],
    ['-v', '--verbose', False, 'verbose output (logging level == INFO)',
        False],
    ['-w', '--veryverbose', False,
        'very verbose output (logging level == DEBUG)', False],
    ['-s', '--silent', False, 'say nothing on mastodon', False],
    ['-c', '--creds_path', 'data/creds.json', 'where to get creds', False]
]
POSITIONAL_ARGUMENTS = [
    # each row is a list with 3 elements: name, type, help text
    ['json_path', str, 'where to get pleiades json']
]
MASTODON_MAX_RATE = 1.1   # 300 requests in 5 minutes == 1 request per second
MASTODON_MIN_RATE = 0.13
MASTODON_MAX_CHARS = 500
wrapper = TextWrapper(
    width=70, initial_indent='     > ', subsequent_indent='     > ')
answer_wrapper = TextWrapper(
    width=70, initial_indent='     > ', subsequent_indent='     > ',
    replace_whitespace=False)
logger = logging.getLogger(__name__)


class Tooter:

    def __init__(self, silent: bool, json_path: str, creds_path: str,
                 max_rate=MASTODON_MAX_RATE, min_rate=MASTODON_MIN_RATE,
                 **kwargs):
        self.api = None
        self.min_period = 1.0/max_rate
        self.max_period = 1.0/min_rate
        self.silent = silent
        if silent:
            logger.warning(
                'Silent mode is engaged. Bot will post nothing to mastodon.')

        # load brain from pleiades json
        path = abspath(realpath(json_path))
        print(
            'I am filling my brain with knowledge from {} ...'.format(
                json_path))
        walker = PleiadesWalker(path=path)
        self.place_count, place_collection = walker.walk()
        self.brain = Brain(place_collection)
        del walker
        print(
            '... done. I know things about {} Pleiades places'.format(
                self.place_count))

        # connect to mastodon
        path = abspath(realpath(creds_path))
        with open(path, 'r') as f:
            creds = json.load(f)
        del f
        api = Mastodon(
            creds['client_id'],
            creds['client_secret'],
            api_base_url=creds['api_base_url']
        )
        email = input(
            'Enter email address for bot account on {}: '.format(
                creds['api_base_url']))
        pwd = getpass.getpass(
            'Enter password for {} on {}: '.format(
                email, creds['api_base_url']))
        try:
            access_token = api.log_in(email, pwd, scopes=['read', 'write'])
        except Mastodon.MastodonUnauthorizedError:
            logger.critical('Login failed: bad credentials.')
            sys.exit(-1)
        del email
        del pwd
        self.api = Mastodon(
            creds['client_id'],
            creds['client_secret'],
            access_token,
            api_base_url=creds['api_base_url']
        )
        del creds
        del access_token
        self._amsg('The bot is in. It is under human supervision.')

    def listen(self, mute=False):
        self._amsg(
            'The bot is listening. It knows about {} #PleiadesGazetteer '
            'places'.format(self.place_count))
        since_path = join('data', 'since_id.txt')
        bak_path = join('data', 'since_id.txt.bak')
        with open(since_path, 'r') as f:
            since_id = f.read().strip()
        del f
        shutil.copy(since_path, bak_path)
        while True:
            period = random.uniform(self.min_period, self.max_period)
            logger.debug('sleeping for {} seconds'.format(period))
            sleep(period)
            logger.debug('awake!')
            notifications = self.api.notifications(since_id=since_id)
            logger.debug(
                'read {} new notifications'.format(len(notifications)))
            for notification in notifications[::-1]:
                self._handle_notification(notification)
            if len(notifications) > 0:
                since_id = notifications[0]['id']
                with open(join('data', 'since_id.txt'), 'w') as f:
                    f.write(str(since_id))
                del f

    def _amsg(self, msg, mute=False, in_reply_to_id=None):
        print(msg)
        if not mute and not self.silent and self.api is not None:
            self.api.status_post(msg, in_reply_to_id=in_reply_to_id)

    def _handle_notification(self, n: dict):
        logger.debug(
            'Notification {} created at: {}'.format(
                n['id'], n['created_at'].isoformat()))
        if n['type'] == 'mention':
            self._handle_mention(n)
        else:
            print(self._serialize(n['type'], n))

    def _serialize(self, dtype: str, d: dict):
        if dtype == 'follow':
            return 'New follow by: {} ({})'.format(
                self._serialize('user', d['account']),
                d['id'])
        if dtype == 'reblog':
            return 'Boost by: {} ({})'.format(
                self._serialize('user', d['account']),
                d['id'])
        if dtype in ['favourite', 'favorite']:
            return 'Favorite by: {} ({})'.format(
                self._serialize('user', d['account']),
                d['id'])
        if dtype == 'user':
            try:
                return '{display_name} ({acct})'.format(**d)
            except KeyError as e:
                logger.fatal(
                    'Expected "{}" in dict:\n{}'.format(
                        e, pformat(d, indent=4)))
                sys.exit(-1)

    def _handle_mention(self, d: dict):
        logger.info('got a mention!')
        who = '@{}'.format(d['account']['acct'])
        soup = BeautifulSoup(d['status']['content'], 'html.parser')
        content = soup.get_text()
        words = content.split()
        content = ' '.join([w for w in words if not w.startswith('@')])
        answer = self.brain.answer(content)
        print(''.ljust(80, '='))
        print('Mention from {}:'.format(
            self._serialize('user', d['account'])))
        print('\n'.join(wrapper.wrap(content)))
        print('My brain thinks a good answer would be:')
        prefix = ''
        if len(answer) > 1:
            prefix = (
                'I know about {} places relevant to your query.\n\n'
                ''.format(len(answer)))

        chunks = []
        if (len(prefix) + len(who) + len('  '.join(answer)) +
                len(answer)*6) > MASTODON_MAX_CHARS:
            if len(answer) == 1:
                raise NotImplementedError(
                    'Single formatted answer is too long.')
            else:
                for a in answer:
                    fa = '{}\n\n'.format(who) + a
                    if len(a) > MASTODON_MAX_CHARS - 10:
                        raise NotImplementedError(
                            'One of the formatted answers is too long: "'
                            '{}"'.format(a))
                    chunks.append(fa)
                for i, chunk in enumerate(chunks):
                    postfix = ''
                    if len(chunks) > 1:
                        postfix = ' {}/{}'.format(i, len(chunks))
                        chunk = '{}{}'.format(chunk, postfix)
                if prefix != '':
                    chunks = [prefix] + chunks
        else:
            chunks = ['{}\n\n{}'.format(who, '\n\n'.join(answer))]
        if len(chunks) > 1:
            print(
                'NB: This answer will be returned in {} chunks'.format(
                    len(chunks)))
            for chunk in chunks:
                print('     > '.ljust(80, '-'))
                print('\n'.join(answer_wrapper.wrap(chunk)))
        else:
            print('\n'.join(answer_wrapper.wrap(chunks[0])))
        verdict = input('Should I post the answer? [y/n]: ')
        if not verdict or verdict.lower() != 'y':
            pass
        else:
            for chunk in chunks:
                self._amsg(chunk, in_reply_to_id=d['id'])
                period = random.uniform(self.min_period, self.min_period * 3.0)
                sleep(period)


def main(**kwargs):
    """
    main function
    """
    tooter = Tooter(**kwargs)
    tooter.listen()

if __name__ == "__main__":
    main(
        **configure_commandline(
            OPTIONAL_ARGUMENTS, POSITIONAL_ARGUMENTS, DEFAULT_LOG_LEVEL))
