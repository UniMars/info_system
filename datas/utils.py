import os
import re

from django.conf import settings


def get_stopwords():
    stop_pattern = re.compile(r'[\s\u2002\u2003\u3000\u200b\u200d\xa0\x7f\d二三四五六七八九.]')
    stopwords = set()
    stopwords_file_path = os.path.join(settings.STATIC_ROOT, 'stopwords.txt')
    with open(stopwords_file_path, 'r', encoding='utf-8') as f:
        for line in f:
            stopwords.add(line.strip())
    return stopwords, stop_pattern
