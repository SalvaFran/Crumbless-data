"""Gluten-free words shared by filter.py and build.py."""
import re
# Gluten-free in many languages (en, de, es, it, pt, nl, fr, pl, fi, sv/da/no, cs/sk, hu, tr, ru, el, zh, ja, ko, ar, he).
GF = re.compile(r'gluten.?fre|glutenfrei|sin gl[uú]ten|sin tacc|senza glutine|sem gl[uú]ten|glutenvrij|sans gluten|bezglutenow|gluteeniton|glutenfri|bezlepkov|glutenmentes|gluténmentes|glutensiz|без\s?глютена|χωρίς γλουτένη|無麩質|无麸质|グルテンフリー|글루텐\s?프리|خالي من الغلوتين|ללא גלוטן|z[öo]liak|celiac|coeliac|cel[ií]ac|celiach', re.I)
