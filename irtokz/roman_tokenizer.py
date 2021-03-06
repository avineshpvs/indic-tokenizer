#!/usr/bin/env python
# -*- coding=utf-8 -*-

from __future__ import (division, unicode_literals)

import re
import os


class RomanTokenizer():

    def __init__(self, split_sen=False):
        self.split_sen = split_sen
        file_path = os.path.abspath(__file__).rpartition('/')[0]

        with open('%s/data/emoticons.txt' % file_path) as fp:
            self.emoticons = set(fp.read().split())

        self.NBP = dict()
        with open('%s/data/NONBREAKING_PREFIXES' % file_path) as fp:
            for line in fp:
                if line.startswith('#'):
                    continue
                if '#NUMERIC_ONLY#' in line:
                    line = line.replace('#NUMERIC_ONLY#', '').split()[0]
                    self.NBP[line] = 2
                else:
                    self.NBP[line.strip()] = 1

        # precompile regexes
        self.fit()

    def fit(self):
        # junk characters
        self.junk = re.compile('[\x00-\x1f]')
        # Latin-1 supplementary characters
        self.latin = re.compile('([\xa1-\xbf\xd7\xf7])')
        # general unicode punctituations except "’"
        self.upunct = re.compile('([\u2012-\u2018\u201a-\u206f])')
        # unicode mathematical operators
        self.umathop = re.compile('([\u2200-\u2211\u2213-\u22ff])')
        # unicode fractions
        self.ufrac = re.compile('([\u2150-\u2160])')
        # unicode superscripts and subscripts
        self.usupsub = re.compile('([\u2070-\u209f])')
        # unicode currency symbols
        self.ucurrency = re.compile('([\u20a0-\u20cf])')
        # all "other" ASCII special characters
        self.specascii = re.compile(r'([\\!@#$%^&*()_+={\[}\]|";:<>?`~/])')

        # keep multiple dots together
        self.multidot = re.compile(r'(\.\.+)([^\.])')
        # seperate "," outside
        self.notanumc = re.compile('([^0-9]),')
        self.cnotanum = re.compile(',([^0-9])')
        # split contractions right (both "'" and "’")
        self.numcs = re.compile("([0-9])'s")
        self.aca = re.compile(
            "([a-zA-Z\u0080-\u024f])'([a-zA-Z\u0080-\u024f])")
        self.acna = re.compile(
            "([a-zA-Z\u0080-\u024f])'([^a-zA-Z\u0080-\u024f])")
        self.nacna = re.compile(
            "([^a-zA-Z\u0080-\u024f])'([^a-zA-Z\u0080-\u024f])")
        self.naca = re.compile(
            "([^a-zA-Z0-9\u0080-\u024f])'([a-zA-Z\u0080-\u024f])")

        # split hyphens
        self.multihyphen = re.compile('(-+)')
        self.hypheninnun = re.compile('(-?[0-9]-+[0-9]-?){,}')
        self.ch_hyp_noalnum = re.compile('(.)-([^a-zA-Z0-9])')
        self.noalnum_hyp_ch = re.compile('([^a-zA-Z0-9])-(.)')
        # restore multi-dots
        self.restoredots = re.compile(r'(DOT)(\1*)MULTI')

        # split sentences
        if self.split_sen:
            self.splitsenr1 = re.compile(' ([.?]) ([A-Z])')
            self.splitsenr2 = re.compile(' ([.?]) ([\'"\(\{\[< ]+) ([A-Z])')
            self.splitsenr3 = re.compile(
                ' ([.?]) ([\'"\)\}\]> ]+) ([A-Z])')

    def normalize_punkt(self, text):
        """replace unicode punctuation by ascii"""
        text = re.sub('[\u2010\u2043]', '-', text)  # hyphen
        text = re.sub('[\u2018\u2019]', "'", text)  # single quotes
        text = re.sub('[\u201c\u201d]', '"', text)  # double quotes
        return text

    def unmask_emos_urls(self, text):
        text = text.split()
        for i, token in enumerate(text):
            if token.startswith('eMoTiCoN-'):
                emo_id = int(token.split('-')[1])
                text[i] = self.emos_dict[emo_id]
            elif token.startswith('sItEuRl-'):
                url_id = int(token.split('-')[1])
                text[i] = self.url_dict[url_id]
        return ' '.join(text)

    def mask_emos_urls(self, text):
        n_e, n_u = 0, 0
        text = text.split()
        self.url_dict = dict()
        self.emos_dict = dict()
        for i, token in enumerate(text):
            if token in self.emoticons:
                text[i] = 'eMoTiCoN-%d' % n_e
                self.emos_dict[n_e] = token
                n_e += 1
            elif token.startswith('http://') or token.startswith('www.'):
                text[i] = 'sItEuRl-%d' % n_u
                self.url_dict[n_u] = token
                n_u += 1
        text = ' '.join(text)
        text = ' %s ' % (text)
        return text

    def tokenize(self, text):
        # unmask emoticons and urls
        text = self.mask_emos_urls(text)
        # normalize unicode punctituation
        text = self.normalize_punkt(text)
        # seperate out on Latin-1 supplementary characters
        text = self.latin.sub(r' \1 ', text)
        # seperate out on general unicode punctituations except "’"
        text = self.upunct.sub(r' \1 ', text)
        # seperate out on unicode mathematical operators
        text = self.umathop.sub(r' \1 ', text)
        # seperate out on unicode fractions
        text = self.ufrac.sub(r' \1 ', text)
        # seperate out on unicode superscripts and subscripts
        text = self.usupsub.sub(r' \1 ', text)
        # seperate out on unicode currency symbols
        text = self.ucurrency.sub(r' \1 ', text)

        # remove ascii junk
        text = self.junk.sub('', text)
        # seperate out all "other" ASCII special characters
        text = self.specascii.sub(r' \1 ', text)

        # keep multiple dots together
        text = self.multidot.sub(lambda m: r' %sMULTI %s' % (
            'DOT' * len(m.group(1)), m.group(2)), text)
        # seperate "," outside
        text = self.notanumc.sub(r'\1 , ', text)
        text = self.cnotanum.sub(r' , \1', text)

        # split contractions right (both "'" and "’")
        text = self.nacna.sub(r"\1 ' \2", text)
        text = self.naca.sub(r"\1 ' \2", text)
        text = self.acna.sub(r"\1 ' \2", text)
        text = self.aca.sub(r"\1 '\2", text)
        text = self.numcs.sub(r"\1 's", text)

        text = text.replace("''", " ' ' ")
        # split dots at word beginings
        text = re.sub(r' (\.+)([^0-9])', r' \1 \2', text)

        # seperate out hyphens
        text = self.multihyphen.sub(
            lambda m: r'%s' % (' '.join(m.group(1))),
            text)
        text = self.hypheninnun.sub(
            lambda m: r'%s' % (m.group().replace('-', ' - ')),
            text)
        text = self.ch_hyp_noalnum.sub(r'\1 - \2', text)
        text = self.noalnum_hyp_ch.sub(r'\1 - \2', text)

        # handle non-breaking prefixes
        words = text.split()
        text_len = len(words) - 1
        text = str()
        for i, word in enumerate(words):
            if word.endswith('.'):
                dotless = word[:-1]
                if dotless.isdigit():
                    word = dotless + ' .'
                elif ('.' in dotless and re.search('[a-zA-Z]', dotless)) or \
                        self.NBP.get(dotless, 0) == 1 or \
                        (i < text_len and words[i + 1][0].islower()):
                    pass
                elif self.NBP.get(dotless, 0) == 2 and \
                        (i < text_len and words[i + 1][0].isdigit()):
                    pass
                elif i < text_len and words[i + 1][0].isdigit():
                    pass
                else:
                    word = dotless + ' .'
            text += "%s " % word

        # restore multi-dots
        text = self.restoredots.sub(lambda m: r'.%s' %
                                    ('.' * int((len(m.group(2)) / 3))),
                                    text)

        # unmask emoticons and urls
        text = self.unmask_emos_urls(text)
        # split sentences
        if self.split_sen:
            text = self.splitsenr1.sub(r' \1\n\2', text)
            text = self.splitsenr2.sub(r' \1\n\2 \3', text)
            text = self.splitsenr3.sub(r' \1 \2\n\3', text)

        return text
