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
from mastodon.Mastodon import MastodonNotFoundError, MastodonUnauthorizedError
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
BLOCK_QUOTE_LEADER = '     > '
wrapper = TextWrapper(
    width=70, initial_indent=BLOCK_QUOTE_LEADER,
    subsequent_indent=BLOCK_QUOTE_LEADER)
answer_wrapper = TextWrapper(
    width=70, initial_indent=BLOCK_QUOTE_LEADER,
    subsequent_indent=BLOCK_QUOTE_LEADER,
    replace_whitespace=False)
logger = logging.getLogger(__name__)
MAX_ANSWER_COUNT = 5


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
        except MastodonUnauthorizedError:
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
            try:
                self.api.status_post(msg, in_reply_to_id=in_reply_to_id)
            except MastodonNotFoundError as e:
                logger.critical(
                    ('\n'.join(
                        (
                            ':'.join([str(a) for a in e.args]),
                            'msg: "{}"'.format(msg),
                            'in_reply_to_id: "{}"'.format(in_reply_to_id)
                        ))))

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

    def _print_block_quote(self, value):
        logger.debug('value: "{}"'.format(value))
        if isinstance(value, str):
            content = value
        elif isinstance(value, list) or isinstance(value, tuple):
            content = '\n'.join(value)
        else:
            raise TypeError(
                '{} cannot work with argument of type {}'
                ''.format('_print_block_instance', type(value)))
        lines = []
        for line in answer_wrapper.wrap(content):
            logger.debug('line: "{}"'.format(line))
            if not line.startswith(BLOCK_QUOTE_LEADER):
                lines.append('{}{}'.format(BLOCK_QUOTE_LEADER, line))
            else:
                lines.append(line)
        logger.debug('lines: "{}"'.format(lines))
        print('\n'.join(lines))

    def _cook_answer(self, raw, querent):
        maximum = MASTODON_MAX_CHARS - 12  # room for multi-part
        words = raw.split()
        word_count = len(words)
        while True:
            reply = '{}\n\n{}'.format(querent, ' '.join(words))
            if len(reply) <= maximum:
                break
            words = words[0:-1]
        if len(words) < word_count:
            reply += ' ...'
        return reply

    def _handle_mention(self, d: dict):
        querent = '@{}'.format(d['account']['acct'])
        query_id = d['id']
        logger.info(
            'got a mention from {} with id="{}"'.format(
                querent, query_id))
        soup = BeautifulSoup(d['status']['content'], 'html.parser')
        query = soup.get_text()
        words = query.split()
        query_content = ' '.join([w for w in words if not w.startswith('@')])
        raw_answers = self.brain.answer(query_content)
        cooked_answers = [
            self._cook_answer(a, querent) for a in raw_answers]
        final_answers = '\n\n'.join(cooked_answers)
        if len(final_answers) < MASTODON_MAX_CHARS:
            final_answers = [final_answers]
        elif len(cooked_answers) == 1:
            raise RuntimeError('this should never happen')
        else:
            answer_count = len(cooked_answers)
            if answer_count > MAX_ANSWER_COUNT:
                final_answers = [self._cook_answer(
                    'I have found {} place resources relevant to your query. '
                    'In order to avoid opprobrium, I am only allowed to '
                    'return the first {} answers. I will provide information '
                    'about each of those place resources in subsequent '
                    'replies.'.format(
                        answer_count, MAX_ANSWER_COUNT), querent)]
            else:
                final_answers = [self._cook_answer(
                    'I have found {} place resources relevant to your query. '
                    'I will provide information about each of them in '
                    'subsequent replies.'.format(answer_count), querent)]
            for i, answer in enumerate(cooked_answers):
                if i >= MAX_ANSWER_COUNT:
                    break
                final_answers.append(
                    '{} {}/{}'.format(
                        answer, i+1, min(answer_count, MAX_ANSWER_COUNT)))

        print(''.ljust(80, '='))
        print('Mention from {} with id="{}":\n'.format(
            self._serialize('user', d['account']), query_id))
        self._print_block_quote(query_content)
        print('\nMy brain thinks a good answer would be:')
        for answer in final_answers:
            print('')
            self._print_block_quote(answer)
        print('')
        verdict = input('Should I post the answer? [y/n]: ')
        if not verdict or verdict.lower() != 'y':
            pass
        else:
            for answer in final_answers:
                print('')
                self._amsg(answer, in_reply_to_id=d['id'])
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
