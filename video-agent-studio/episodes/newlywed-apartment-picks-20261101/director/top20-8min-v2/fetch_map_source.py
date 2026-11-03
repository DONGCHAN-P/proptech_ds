"""Freeze openly licensed, period-matched geography without altering old assets."""
import gzip
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[5]
EP = Path(__file__).resolve().parents[2]
OUT = EP / "research/top20-8min-v2/source"


def fetch(url):
    with urlopen(Request(url, headers={"User-Agent": "RealEstateResearch/1.0 (public visual research)"}), timeout=45) as r:
        return r.read()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    urls = {
        "geometry": "https://raw.githubusercontent.com/vuski/admdongkor/master/ver20241001/HangJeongDong_ver20241001.geojson",
        "license": "https://raw.githubusercontent.com/vuski/admdongkor/master/LICENSE-DATA",
        "newlyweds_2023": "https://sri.kostat.go.kr/boardDownload.es?bid=11815&list_no=434122&seq=3",
    }
    with ThreadPoolExecutor(max_workers=3) as pool:
        tasks = {key: pool.submit(fetch, value) for key, value in urls.items()}
        results = {key: task.result() for key, task in tasks.items()}
    raw = results["geometry"]
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    assert blob == "0f308e8a90fb960e298f2f28582fb87ba68c070e", blob
    data = json.loads(raw)
    (OUT / "HangJeongDong_ver20241001.geojson.gz").write_bytes(gzip.compress(raw, mtime=0))
    (OUT / "LICENSE-DATA.txt").write_bytes(results["license"])
    assert results["newlyweds_2023"].startswith(b"%PDF")
    (OUT / "newlyweds_2023.pdf").write_bytes(results["newlyweds_2023"])
    metadata = {"retrieved_at": datetime.now().astimezone().isoformat(), "boundary_version": "2024-10-01",
      "boundary_git_blob_sha1": blob, "license": "CC BY 4.0; upstream SGIS KOGL Type 1 attribution retained",
      "raw_geometry_preservation": "lossless gzip, original UTF-8 bytes recoverable", "sources": {
        key: {"url": urls[key], "raw_bytes": len(value), "sha256": hashlib.sha256(value).hexdigest()} for key,value in results.items()
      }}
    (OUT / "source_manifest.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"features": len(data["features"]), "properties_examples": [x["properties"] for x in data["features"][:3]],
      "compressed_bytes": (OUT / "HangJeongDong_ver20241001.geojson.gz").stat().st_size,
      "git_blob_verified": blob}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
