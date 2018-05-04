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
    'active'
]

directives = {
    'list': {
        'triggers': ['list'],
        'handler': 'listing',
        'matchers': [
            re.compile(r'^(list|listing) (?P<tokens>.+)$')
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


class Brain:

    def __init__(self, place_collection):
        self.place_collection = place_collection

    def answer(self, question):
        clean_question = self._clean(question)
        logger.debug('clean_question: "{}"'.format(clean_question))
        words = clean_question.split()

        if len(words) == 1:
            if words[0] == 'ping':
                return ['pong']
            answer = self._do_answer_listing(words)
            if len(answer) != 0:
                return answer
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
        return ["Sorry, I don't understand the question."]

    def _do_answer_age(self, tokens: list):
        return ["Sorry, I can't do time-period answers yet."]

    def _do_answer_listing(self, tokens: list):
        results = []
        for token in tokens:
            try:
                pid = int(token)
            except ValueError:
                pass
            else:
                if str(pid) == token:
                    results.extend(
                        self.place_collection.get('id', token))
                    continue
            results.extend(self.place_collection.get('name', token))
        return [str(r) for r in results]

    def _do_answer_most_recent(self, tokens: list):
        # NB: tokens are ignored
        results = self.place_collection.get('last_modified')
        if len(results) > 1:
            i = random.randint(0, len(results)-1)
            prefix = (
                'I know about {} recently changed place resources. One of '
                'them is:'.format(len(results)))
            answer = [prefix, str(results[i])]
        else:
            answer = [str(results[0])]
        return answer


    def _clean(self, raw):
        cooked = raw
        cooked = textnorm.normalize_space(cooked)
        cooked = textnorm.normalize_unicode(cooked, 'NFD')
        cooked = cooked.translate(punct_table)
        cooked = textnorm.normalize_unicode(cooked, 'NFC')
        cooked = cooked.lower()
        cooked = ' '.join([c for c in cooked.split() if c not in IGNORE])
        return cooked
