#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python 3 script template (changeme)
"""

import better_exceptions
from itertools import permutations
import logging
from pyfiglet import Figlet, FontNotFound
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
                r'^(recent|latest|most recent|recently modified|last|'
                'most recently modified|latest updates)$')
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

        if ('superluminal' in clean_question or
                'beamship' in clean_question or
                'phase conjugate' in clean_question or
                'reverse time travel' in clean_question or
                'ophanim' in clean_question or
                'wingmakers' in clean_question or
                'starseed' in clean_question or
                'golden ratio' in clean_question):
            return self._do_answer_superluminal()
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
            logger.debug('directive key: {}'.format(key))
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
#        for trigger in triggers:
#            clean_question = clean_question.replace(trigger, '')
        answer = self._do_answer_named([clean_question])
        if len(answer) == 0:
            answer = self._do_answer_named(clean_question.split())
        return answer

    def _do_answer_superluminal(self):
        superfluities = [
            'Sterope', 'Merope', 'Electra', 'Maia', 'Taygeta', 'Celaeno',
            'Alcyone', 'Atlas', 'Pleione', 'Eta (25) Tauri', '27 Tauri',
            '17 Tauri', '20 Tauri', '23 Tauri', '19 Tauri', '28 (BU) Tauri',
            '16 Tauri', 'Asterope', '21 Tauri', '22 Tauri', '18 Tauri',
            'Seven Sisters', 'Messier 45', 'Atlantides', 'Vergiliae',
            'Matariki', 'Krittika', 'Thurayya', 'MULMUL', 'Mutsuraboshi',
            'Subaru', '1610', 'Con†Stellation', 'NASFA',
            'https://en.wikipedia.org/wiki/Pleiades',
            'https://scaife.perseus.org/search/?kind=form&p=3&q=pleiades',
            'https://scaife.perseus.org/search/?q=%CE%A0%CE%BB%CE%B5%CE%B9%CE%AC%CE%B4%CE%B5%CF%82&kind=lemma'
            ]
        fonts = ['1row', '3-d', '3d_diagonal', '3x5', '4max', '4x4_offr', '5lineoblique', '5x7', '5x8', '64f1____', '6x10', '6x9', 'B1FF', 'DANC4', 'ICL-1900', 'a_zooloo', 'acrobatic', 'advenger', 'alligator', 'alligator2', 'alligator3', 'alpha', 'alphabet', 'amc3line', 'amc3liv1', 'amcaaa01', 'amcneko', 'amcrazo2', 'amcrazor', 'amcslash', 'amcslder', 'amcthin', 'amctubes', 'amcun1', 'aquaplan', 'arrows', 'asc_____', 'ascii9', 'ascii___', 'ascii_new_roman', 'assalt_m', 'asslt__m', 'atc_____', 'atc_gran', 'avatar', 'b_m__200', 'banner', 'banner3-D', 'banner3', 'banner4', 'barbwire', 'basic', 'battle_s', 'battlesh', 'baz__bil', 'bear', 'beer_pub', 'bell', 'benjamin', 'big', 'bigascii12', 'bigascii9', 'bigchief', 'bigfig', 'bigmono12', 'bigmono9', 'binary', 'block', 'blocks', 'bolger', 'braced', 'bright', 'brite', 'briteb', 'britebi', 'britei', 'broadway', 'broadway_kb', 'bubble', 'bubble__', 'bubble_b', 'bulbhead', 'c1______', 'c2______', 'c_ascii_', 'c_consen', 'calgphy2', 'caligraphy', 'cards', 'catwalk', 'caus_in_', 'char1___', 'char2___', 'char3___', 'char4___', 'charact1', 'charact2', 'charact3', 'charact4', 'charact5', 'charact6', 'characte', 'charset_', 'chartr', 'chartri', 'chiseled', 'chunky', 'circle', 'clb6x10', 'clb8x10', 'clb8x8', 'cli8x8', 'clr4x6', 'clr5x10', 'clr5x6', 'clr5x8', 'clr6x10', 'clr6x6', 'clr6x8', 'clr7x10', 'clr7x8', 'clr8x10', 'clr8x8', 'coil_cop', 'coinstak', 'cola', 'colossal', 'com_sen_', 'computer', 'contessa', 'contrast', 'convoy__', 'cosmic', 'cosmike', 'cour', 'courb', 'courbi', 'couri', 'crawford', 'crazy', 'cricket', 'cursive', 'cyberlarge', 'cybermedium', 'cybersmall', 'cygnet', 'd_dragon', 'dancingfont', 'dcs_bfmo', 'decimal', 'deep_str', 'defleppard', 'demo_1__', 'demo_2__', 'demo_m__', 'devilish', 'diamond', 'dietcola', 'digital', 'doh', 'doom', 'dosrebel', 'dotmatrix', 'double', 'doubleshorts', 'drpepper', 'druid___', 'dwhistled', 'e__fist_', 'ebbs_1__', 'ebbs_2__', 'eca_____', 'eftichess', 'eftifont', 'eftipiti', 'eftirobot', 'eftitalic', 'eftiwall', 'eftiwater', 'emboss', 'emboss2', 'epic', 'etcrvs__', 'f15_____', 'faces_of', 'fair_mea', 'fairligh', 'fantasy_', 'fbr12___', 'fbr1____', 'fbr2____', 'fbr_stri', 'fbr_tilt', 'fender', 'filter', 'finalass', 'fire_font-k', 'fire_font-s', 'fireing_', 'flipped', 'flowerpower', 'flyn_sh', 'fourtops', 'fp1_____', 'fp2_____', 'fraktur', 'funface', 'funfaces', 'funky_dr', 'future', 'future_1', 'future_2', 'future_3', 'future_4', 'future_5', 'future_6', 'future_7', 'future_8', 'fuzzy', 'gauntlet', 'georgi16', 'georgia11.flf ', 'ghost', 'ghost_bo', 'ghoulish', 'glenyn', 'goofy', 'gothic', 'gothic__', 'graceful', 'gradient', 'graffiti', 'grand_pr', 'greek', 'green_be', 'hades___', 'heart_left', 'heart_right', 'heavy_me', 'helv', 'helvb', 'helvbi', 'helvi', 'henry3d', 'heroboti', 'hex', 'hieroglyphs', 'high_noo', 'hills___', 'hollywood', 'home_pak', 'horizontalleft', 'horizontalright', 'house_of', 'hypa_bal', 'hyper___', 'impossible', 'inc_raw_', 'invita', 'isometric1', 'isometric2', 'isometric3', 'isometric4', 'italic', 'italics_', 'ivrit', 'jacky', 'jazmine', 'jerusalem', 'joust___', 'katakana', 'kban', 'keyboard', 'kgames_i', 'kik_star', 'knob', 'konto', 'kontoslant', 'krak_out', 'larry3d', 'lazy_jon', 'lcd', 'lean', 'letter', 'letter_w', 'letters', 'letterw3', 'lexible_', 'lildevil', 'lineblocks', 'linux', 'lockergnome', 'mad_nurs', 'madrid', 'magic_ma', 'marquee', 'master_o', 'maxfour', 'mayhem_d', 'mcg_____', 'merlin1', 'merlin2', 'mig_ally', 'mike', 'mini', 'mirror', 'mnemonic', 'modern__', 'modular', 'mono12', 'mono9', 'morse', 'morse2', 'moscow', 'mshebrew210', 'muzzle', 'nancyj-fancy', 'nancyj-improved', 'nancyj-underlined', 'nancyj', 'new_asci', 'nfi1____', 'nipples', 'notie_ca', 'npn_____', 'nscript', 'ntgreek', 'nvscript', 'o8', 'octal', 'odel_lak', 'ogre', 'ok_beer_', 'oldbanner', 'os2', 'outrun__', 'p_s_h_m_', 'p_skateb', 'pacos_pe', 'pagga', 'panther_', 'pawn_ins', 'pawp', 'peaks', 'peaksslant', 'pebbles', 'pepper', 'phonix__', 'platoon2', 'platoon_', 'pod_____', 'poison', 'puffy', 'puzzle', 'pyramid', 'r2-d2___', 'rad_____', 'rad_phan', 'radical_', 'rainbow_', 'rally_s2', 'rally_sp', 'rammstein', 'rampage_', 'rastan__', 'raw_recu', 'rci_____', 'rectangles', 'red_phoenix', 'relief', 'relief2', 'rev', 'reverse', 'ripper!_', 'road_rai', 'rockbox_', 'rok_____', 'roman', 'roman___', 'rot13', 'rot13', 'rotated', 'rounded', 'rowancap', 'rozzo', 'runic', 'runyc', 's-relief', 'sans', 'sansb', 'sansbi', 'sansi', 'santaclara', 'sblood', 'sbook', 'sbookb', 'sbookbi', 'sbooki', 'script', 'script__', 'serifcap', 'shadow', 'shimrod', 'short', 'skate_ro', 'skateord', 'skateroc', 'sketch_s', 'slant', 'slide', 'slscript', 'sm______', 'small', 'smallcaps', 'smascii9', 'smblock', 'smbraille', 'smisome1', 'smkeyboard', 'smmono12', 'smmono9', 'smpoison', 'smscript', 'smshadow', 'smslant', 'smtengwar', 'soft', 'space_op', 'spc_demo', 'speed', 'spliff', 'stacey', 'stampate', 'stampatello', 'standard', 'star_war', 'starstrips', 'starwars', 'stealth_', 'stellar', 'stencil1', 'stencil2', 'stforek', 'stop', 'straight', 'street_s', 'sub-zero', 'subteran', 'super_te', 'swampland', 'swan', 'sweet', 't__of_ap', 'tanja', 'tav1____', 'taxi____', 'tec1____', 'tec_7000', 'tecrvs__', 'tengwar', 'term', 'test1', 'thick', 'thin', 'threepoint', 'ti_pan__', 'ticks', 'ticksslant', 'tiles', 'times', 'timesofl', 'tinker-toy', 'tomahawk', 'tombstone', 'top_duck', 'train', 'trashman', 'trek', 'triad_st', 'ts1_____', 'tsalagi', 'tsm_____', 'tsn_base', 'tty', 'ttyb', 'tubular', 'twin_cob', 'twisted', 'twopoint', 'type_set', 'ucf_fan_', 'ugalympi', 'unarmed_', 'univers', 'upper', 'usa_____', 'usa_pq__', 'usaflag', 'utopia', 'utopiab', 'utopiabi', 'utopiai', 'varsity', 'vortron_', 'war_of_w', 'wavy', 'weird', 'wetletter', 'whimsy', 'wideterm', 'wow', 'xbrite', 'xbriteb', 'xbritebi', 'xbritei', 'xchartr', 'xchartri', 'xcour', 'xcourb', 'xcourbi', 'xcouri', 'xhelv', 'xhelvb', 'xhelvbi', 'xhelvi', 'xsans', 'xsansb', 'xsansbi', 'xsansi', 'xsbook', 'xsbookb', 'xsbookbi', 'xsbooki', 'xtimes', 'xtty', 'xttyb', 'yie-ar__', 'yie_ar_k', 'z-pilot_', 'zig_zag_', 'zone7___']
        i = random.randint(0, len(superfluities)-1)
        s = superfluities[i]
        if 'http' in s:
            return [s]
        else:
            j = random.randint(0, len(fonts)-1)
            try:
                f = Figlet(font=fonts[j])
            except FontNotFound:
                f = Figlet(font='block')
            return [f.renderText(s)]

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

    def _generate_name_candidates(self, tokens: list):
        if len(tokens) == 1:
            candidates = tokens
        else:
            candidates = [' '.join(t) for t in list(permutations(tokens))]
        return candidates

    def _do_answer_named(self, tokens: list):
        results = []
        candidates = self._generate_name_candidates(tokens)
        for candidate in candidates:
            results.extend(self.place_collection.get('name', candidate))
            results.extend(self.place_collection.get('in_name', candidate))
        results = list(set(results))
        logger.debug('{} results in hand'.format(len(results)))
        return self._handle_multiples('list named', results, tokens)

    def _do_answer_list_named(self, tokens: list):
        results = []
        candidates = self._generate_name_candidates(tokens)
        for candidate in candidates:
            results.extend(self.place_collection.get('name', candidate))
            results.extend(self.place_collection.get('in_name', candidate))
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
