"""Compare exact encoded frames of the old and new Shorts."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

D = Path(__file__).resolve().parent
E = D.parents[2]
OLD = E / 'qa/top20-split-v4/jun-and-shorts-v1/encoded/SHORT03-R15-R11-v4/encoded_manifest.json'
NEW = E / 'qa/top20-split-v4/shorts-ui-v2-20261104/encoded/SHORT03-R15-R11/encoded_manifest.json'


def main():
    old = json.loads(OLD.read_text(encoding='utf-8'))
    new = json.loads(NEW.read_text(encoding='utf-8'))
    out = E / 'outputs/top20-split-v4/shorts-ui-v2-20261104'
    font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 28)
    sheet = Image.new('RGB', (1440, 1420), '#f6f4ef')
    dr = ImageDraw.Draw(sheet)
    cases = [('도입', 'first'), ('가격 비교', 'region_last'), ('마무리', 'cta_last')]
    records = []
    for col, (title, purpose) in enumerate(cases):
        for row, (label, data) in enumerate([('기존 출력본', old), ('개선 출력본', new)]):
            frame = next(x for x in data['frames'] if
                         (x['purpose'].endswith('_first') if purpose == 'first' else x['purpose'] == purpose))
            if purpose == 'first' and row == 1:
                frame = next(x for x in data['frames'] if x['purpose'] == 'first_frame')
            im = Image.open(frame['file']).convert('RGB')
            im.thumbnail((360, 640))
            x, y = col * 480 + 60, row * 710 + 48
            sheet.paste(im, (x, y))
            dr.text((x, y - 38), f'{label} · {title} · {frame["time_s"]:.2f}s', font=font, fill='#142e42')
            records.append(dict(frame, label=label, comparison_role=title, video_sha256=data['video_sha256']))
    out.mkdir(parents=True, exist_ok=True)
    image = out / 'UI_전후비교.jpg'
    sheet.save(image, quality=95)
    (D / 'comparison_manifest.json').write_text(json.dumps(dict(
        status='actual_encoded_comparison_ready', image=str(image), frames=records),
        ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(str(image))


if __name__ == '__main__':
    main()
