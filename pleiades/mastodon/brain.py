#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python 3 script template (changeme)
"""

import better_exceptions
import logging
import random
import re
import sys
import textnorm
import unicodedata

logger = logging.getLogger(__name__)
punct_table = dict.fromkeys(
    i for i in range(sys.maxunicode)
    if unicodedata.category(chr(i)).startswith('P'))

IGNORE = [
    'please',
    'give',
    'me',
    'a',
    'of',
    'place',
    'places',
    'what',
    'is',
    'the',
    'are',
    'which',
    'was',
    'active',
    'were'
]

directives = {
    'list_latest': {
        'triggers': ['list latest', 'list recent', 'list last modified',
                     'list most recent', 'list latest updates'],
        'handler': 'listing_latest',
        'matchers': [
            re.compile(
                r'^list (latest|recent|most recent|last modified|latest '
                'updates)$')
        ]
    },
    'named': {
        'triggers': ['name', 'named', 'called'],
        'handler': 'named',
        'matchers': [
            re.compile(r'^(name|named|called) (?P<tokens>.+)$')
        ]
    },
    'pid': {
        'triggers': ['pid', 'pleiades id', 'pleiades uri', 'http', 'id'],
        'handler': 'pid',
        'matchers': [
            re.compile(r'^(pid|pleiades id|id) (?P<tokens>.+)$'),
            re.compile(
                r'^(pid|pleiades id|id|pleiades uri|uri) '
                r'https?://pleiades\.stoa\.org/places/(?P<tokens>\d+)/?$')
        ]
    },
    'list_named': {
        'triggers': ['list named'],
        'handler': 'list_named',
        'matchers': [
            re.compile(r'^(list named) (?P<tokens>.+)$')
        ]
    },
    'list_pid': {
        'triggers': ['list pid'],
        'handler': 'list_pid',
        'matchers': [
            re.compile(r'^(list pid) (?P<tokens>.+)$')
        ]
    },
    'latest': {
        'triggers': ['latest', 'recent', 'modified', 'last', 'update'],
        'handler': 'most_recent',
        'matchers': [
            re.compile(
                r'^(latest|most recent|recently modified|last|most recently '
                'modified|latest updates)$')
        ]
    },
    'age': {
        'triggers': ['age', 'old', 'when'],
        'handler': 'age',
        'matchers': [
            re.compile(r'^(how old|when|age) (?P<tokens>.+)$')
        ]
    }
}
triggers = []
for k, d in directives.items():
    triggers.extend(d['triggers'])
triggers = list(set(triggers))
triggers.sort(key=len)


class Brain:

    def __init__(self, place_collection):
        self.place_collection = place_collection

    def answer(self, question):
        clean_question = self._clean(question)
        logger.debug('clean_question: "{}"'.format(clean_question))

        if ' ' not in clean_question:
            if clean_question == 'ping':
                return ['pong']
            else:
                try:
                    pid = int(clean_question)
                except ValueError:
                    pass
                else:
                    if str(pid) == clean_question:
                        return self._do_answer_pid([clean_question])
        for key, directive in directives.items():
            logger.debug('key: {}'.format(key))
            for trigger in directive['triggers']:
                logger.debug('trigger: {}'.format(trigger))
                if trigger in clean_question:
                    for matcher in directive['matchers']:
                        logger.debug('matcher: {}'.format(matcher.pattern))
                        m = matcher.match(clean_question)
                        if m is not None:
                            logger.debug('match')
                            try:
                                tokens = m.group('tokens').split()
                            except IndexError:
                                tokens = []
                            return getattr(
                                self,
                                '_do_answer_{}'.format(
                                    directive['handler']))(tokens)
                        else:
                            logger.debug('miss')
        for trigger in triggers:
            clean_question = clean_question.replace(trigger, '')
        answer = self._do_answer_named([clean_question])
        if len(answer) == 0:
            answer = self._do_answer_named(clean_question.split())
        return answer

    def _do_answer_age(self, tokens: list):
        return ["Sorry, I can't do time-period answers yet."]

    def _do_answer_listing_latest(self, tokens: list):
        # NB: tokens are ignored
        results = self.place_collection.get('last_modified')
        return [str(r) for r in results]

    def _handle_multiples(self, trigger: str, results: list, tokens: list):
        if len(results) > 1:
            i = random.randint(0, len(results)-1)
            prefix = (
                'I know about {} places relevant to your query. One of them '
                'is:'.format(len(results)))
            postfix = (
                'For all matches, reply with "{} {}"'.format(
                    trigger, ' '.join(tokens))).strip()
            answer = ['\n\n'.join((prefix, str(results[i]), postfix))]
        else:
            answer = [str(r) for r in results]
        logger.debug(answer)
        return answer

    def _do_answer_named(self, tokens: list):
        results = []
        for token in tokens:
            results.extend(self.place_collection.get('name', token))
            results.extend(self.place_collection.get('in_name', token))
        results = list(set(results))
        logger.debug('{} results in hand'.format(len(results)))
        return self._handle_multiples('list named', results, tokens)

    def _do_answer_list_named(self, tokens: list):
        results = []
        for token in tokens:
            results.extend(self.place_collection.get('name', token))
            results.extend(self.place_collection.get('in_name', token))
        results = list(set(results))
        return [str(r) for r in results]

    def _do_answer_pid(self, tokens: list):
        results = []
        for token in tokens:
            results.extend(self.place_collection.get('id', token))
        return self._handle_multiples('list pid', results, tokens)

    def _do_answer_most_recent(self, tokens: list):
        # NB: tokens are ignored
        results = self.place_collection.get('last_modified')
        return self._handle_multiples('list latest', results, [])

    def _clean(self, raw):
        cooked = raw
        cooked = textnorm.normalize_space(cooked)
        cooked = textnorm.normalize_unicode(cooked, 'NFD')
        cooked = cooked.translate(punct_table)
        cooked = textnorm.normalize_unicode(cooked, 'NFC')
        cooked = cooked.lower()
        cooked = ' '.join([c for c in cooked.split() if c not in IGNORE])
        return cooked
