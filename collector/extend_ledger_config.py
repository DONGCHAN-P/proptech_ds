from pathlib import Path
p=Path('collector/collect_three_cities.py');s=p.read_text(encoding='utf-8-sig');s=s.replace("def stamp():", "LEDGER=OUT\n\ndef stamp():");s=s.replace("ledger=OUT/f'calls-{day}.json'", "ledger=LEDGER/f'calls-{day}.json'");p.write_text(s,encoding='utf8')
