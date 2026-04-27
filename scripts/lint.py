#!/usr/bin/env python3

from time import sleep
import threading
from typing import Generator
import os
import lxml.etree
from lxml.etree import Element
import sys
import requests
import json
import logging

ns = {
    "josm": "http://josm.openstreetmap.de/tagging-preset-1.0"
}

DEFAULT_LANG = "ka"
LANGS = [ "en", "ru", "ka" ]

class Issue:
    item : Element | None = None

    def __init__(self, message, severity=logging.WARN, item=None, tag=None):
        self.message = message
        self.item = item
        self.tag = tag
        self.severity = severity

    def location(self):
        if self.tag is not None:
            return self.tag.sourceline
        elif self.item is not None:
            return self.item.sourceline
        else:
            return "<unknown>"

def issues_with_item(item, issues):
    for issue in issues:
        issue.item = item
        yield issue

def issues_with_tag(tag, issues):
    for issue in issues:
        issue.tag = tag
        yield issue

def item_tags(item: Element) -> dict:
    tags = {}
    for key in item.findall('josm:key', ns):
        tags[key.attrib["key"]] = key.attrib["value"]
    return tags

wikidata_cache = {}

def fetch_wikidata_qid(qid: str) -> dict:
    if qid in wikidata_cache:
        return wikidata_cache[qid]
    else:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'}
        url = f"https://www.wikidata.org/w/rest.php/wikibase/v1/entities/items/{qid}"
        resp = requests.get(url, headers=headers)
        while resp.status_code == 429:
            delay = int(resp.headers["retry-after"])
            logging.debug(f"Note: too many wikidata requests, backing off for {delay}")
            sleep(delay)
            resp = requests.get(url, headers=headers)

        obj = json.loads(resp.text)
        wikidata_cache[qid] = obj
        return obj


def match_values(name1, value1, name2, value2) -> Generator[Issue]:
    if value1 is not None and value2 is not None and value1 != value2:
        yield Issue(f"{name1} ({value1}) does not match {name2} ({value2})")

def check_wikidata_tag(wd: dict, item, key: str, lang: str) -> Generator[Issue]:
    for k in filter(lambda x: x.attrib["key"] == key, item.findall("josm:key", ns)):
        name = k.attrib["value"]
        if not (
            "labels" not in wd or lang not in wd["labels"] or name == wd["labels"][lang]
            or "aliases" not in wd or lang not in wd["aliases"] or name in wd["aliases"][lang]
            ):
                yield Issue(
                            f"{key} ({name}) is neither a label ({wd.get("labels", {}).get(lang, "<no label>")}) nor an alias ({", ".join(wd.get("aliases", {}).get(lang, []))}) of wikidata item {wd["id"]} in language {lang}",
                            tag = item,
                        )

def check_wikidata_family(item: Element, tag_family: str):
    qid = item_tags(item).get(f"{tag_family}:wikidata", None)
    if qid:
        wd = fetch_wikidata_qid(qid)
        for lang in LANGS:
            key = f"{tag_family}:{lang}"
            yield from check_wikidata_tag(wd, item, key, lang)

def check_wikidata(item):
    yield from check_wikidata_family(item, "brand")
    yield from check_wikidata_family(item, "operator")

def check_tag_kartuli(item: Element, tag_family: str):
    tags = item_tags(item)
    l = f"{tag_family}:{DEFAULT_LANG}"
    if tag_family in tags and l in tags:
        yield from issues_with_tag(item, match_values(f"tag {tag_family}", tags[tag_family], f"tag {l}", tags[l]))

def check_names_kartuli(item):
    yield from check_tag_kartuli(item, "brand")
    yield from check_tag_kartuli(item, "operator")

def check_group(group: Element, diff_map: dict):
    for item in group.findall('josm:item', ns):
        name = item.attrib["name"]
        if name not in diff_map or item_tags(item) != diff_map[name]:
            for check in [check_names_kartuli, check_wikidata]:
                yield from issues_with_item(item, check(item))
        else:
            logging.debug(f"Item {name} has not changed, skip")

    for subgroup in group.findall('josm:group', ns):
        yield from check_group(subgroup, diff_map)

def prepare_item_map(group: Element):
    map = {}
    for item in group.findall('josm:item', ns):
        map[item.attrib["name"]] = item_tags(item)

    for subgroup in group.findall('josm:group', ns):
        map = map | prepare_item_map(subgroup)

    return map

def __main__():
    diff_map = {}
    if len(sys.argv) > 2:
        diff_group = lxml.etree.parse(open(sys.argv[2], "r")).getroot().find("josm:group", ns)
        if diff_group is not None:
            diff_map = prepare_item_map(diff_group)

    exit_code = 0

    input_file = sys.argv[1]
    root_group = lxml.etree.parse(open(input_file, "r")).getroot().find("josm:group", ns)
    if root_group is not None:
        for issue in check_group(root_group, diff_map):
            print(f"{input_file}#{issue.location()}: {logging.getLevelName(issue.severity)}: {issue.item.attrib["name"]}: {issue.message}")
            exit_code = 1

    exit(exit_code)

__main__()
