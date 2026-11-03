"""Add the shared video call policy pointer without changing role/model settings."""
from pathlib import Path
import argparse
import tomllib

ROOT=Path(__file__).resolve().parents[1]
LINE='호출 효율은 studio_root/guides/호출_효율_운영.md 및 config/video_call_policy.json을 따른다. 짧은 task packet만 전달하고, 반복 상태 확인·진행 메시지·불변 자료 재검수를 피한다. 실제 승인·독립 검수·필수 증거는 유지한다.\n'

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--native',action='store_true');args=parser.parse_args()
    directory=ROOT/('.codex/agents' if args.native else 'video-agent-studio/agents')
    changed=0
    for path in sorted(directory.glob('video_*.toml')):
        text=path.read_text(encoding='utf-8-sig')
        if LINE.strip() not in text:
            marker='developer_instructions = """\n'
            if marker not in text:raise ValueError(f'Unexpected role format: {path.name}')
            text=text.replace(marker,marker+LINE,1)
            tomllib.loads(text)
            path.write_text(text,encoding='utf8');changed+=1
    print(f'Role policy links: {directory.name}; changed={changed}')
