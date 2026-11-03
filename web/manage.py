"""Local administrator commands: aggregated counters or retention cleanup."""
import argparse
import json
from web.service_api import get_store

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['stats', 'prune'])
    args = parser.parse_args()
    store = get_store()
    if args.action == 'prune':
        store.prune()
        print('Expired sessions, old events and request logs removed.')
    else:
        print(json.dumps(store.stats(), ensure_ascii=False, indent=2))
