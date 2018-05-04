#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Command line interface to the bot.
"""

from airtight.cli import configure_commandline
import logging
from os.path import abspath, realpath
from pleiades.mastodon.brain import Brain
from pleiades.walker.walker import PleiadesWalker


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
        'very verbose output (logging level == DEBUG)', False]
]
POSITIONAL_ARGUMENTS = [
    # each row is a list with 3 elements: name, type, help text
    ['json_path', str, 'path to Pleiades JSON tree']
]

logger = logging.getLogger(__name__)


def main(**kwargs):
    """
    main function
    """
    # logger = logging.getLogger(sys._getframe().f_code.co_name)
    print('I am learning ...')
    path = abspath(realpath(kwargs['json_path']))
    walker = PleiadesWalker(path=path)
    place_count, place_collection = walker.walk()
    brain = Brain(place_collection)
    print('done. I know things about {} Pleiades places'.format(place_count))
    print('Feel free to ask me a question.')
    while True:
        question = input('? ')
        answers = brain.answer(question)
        for answer in answers:
            print('\n{}'.format(answer))


if __name__ == "__main__":
    main(
        **configure_commandline(
            OPTIONAL_ARGUMENTS, POSITIONAL_ARGUMENTS, DEFAULT_LOG_LEVEL))
