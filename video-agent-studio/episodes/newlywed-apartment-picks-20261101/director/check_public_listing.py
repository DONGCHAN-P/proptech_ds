"""Inspect public page structure; never bypass a login or blocked response."""
from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import urlopen

OUT = Path(__file__).resolve().parent.parent / "research/public_page_checks"


class Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.current = {"attrs": dict(attrs), "body": ""}

    def handle_data(self, data):
        if self.current is not None:
            self.current["body"] += data

    def handle_endtag(self, tag):
        if tag == "script" and self.current is not None:
            self.items.append(self.current)
            self.current = None


def main():
    url = "https://town.aipartner.com/memul/T272013181"
    if "--local" in sys.argv:
        text = (OUT / "aipartner_T272013181.html").read_text(encoding="utf-8")
        status = "saved_public_http_200"
    else:
        with urlopen(url, timeout=25) as response:
            text = response.read().decode("utf-8")
            status = response.status
    OUT.mkdir(exist_ok=True)
    (OUT / "aipartner_T272013181.html").write_text(text, encoding="utf-8")
    parser = Scripts()
    parser.feed(text)
    print(json.dumps({"http_status": status, "html_characters": len(text), "script_count": len(parser.items)}, ensure_ascii=False))
    flight = []
    for item in parser.items:
        body = item["body"]
        marker = "self.__next_f.push("
        if marker in body:
            try:
                payload, _ = json.JSONDecoder().raw_decode(body.split(marker, 1)[1])
            except ValueError:
                continue
            if isinstance(payload, list) and len(payload) > 1 and isinstance(payload[1], str):
                value = payload[1]
                flight.append(value)
        if item["attrs"].get("type") == "application/json" or item["attrs"].get("id") in {"__NEXT_DATA__", "__NUXT_DATA__"}:
            try:
                data = json.loads(item["body"])
            except ValueError:
                continue
            (OUT / "aipartner_public_state.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print("public_json", type(data).__name__, list(data)[:15] if isinstance(data, dict) else len(data))
    def walk(value):
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from walk(child)
        elif isinstance(value, list):
            for child in value:
                yield from walk(child)
    for line in "".join(flight).splitlines():
        _, _, raw = line.partition(":")
        if not raw.startswith(("{", "[")):
            continue
        try:
            state = json.loads(raw)
        except ValueError:
            continue
        for obj in walk(state):
            if "tradePrice" in obj and "useMeter" in obj:
                print("article_field_names", list(obj))
                keys = {"articleCd", "articleNo", "tradePrice", "meter1", "meter2", "useMeter", "businessDivNm", "dongNm", "hoNm", "floor", "totalFloor", "direction", "registerDate", "modifyDate", "confirmDate", "regDt", "updDt", "regDtm", "updDtm", "articleStatus", "articleStatusNm", "buildYear", "corrpFlr", "groundFlr", "dWay", "displayYn", "firstPriceHstrInfos", "priceHstrInfos", "intoDay", "intoHyubiYn", "moveinTypeCode"}
                filtered = {key: val for key, val in obj.items() if key in keys or any(s in key.lower() for s in ["date", "dtm", "status", "floor", "direction", "dong", "publish"])}
                (OUT / "aipartner_article_fields.json").write_text(json.dumps(filtered, ensure_ascii=False, indent=2), encoding="utf-8")
                print(json.dumps(filtered, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
