"""Persistent caption rails, hidden during brand inserts and the final silent hold."""
def body_windows(scenes,last_word):
    windows=[]
    for s in scenes:
        if not s.get('sentences'):continue
        start,end=s['start_s'],min(s['end_s'],last_word)
        if end<=start:continue
        if windows and start<=windows[-1][1]+.0001:windows[-1][1]=max(windows[-1][1],end)
        else:windows.append([start,end])
    return windows

def markup(windows,prefix,portrait=False):
    x,y,w,h=(140,1100,700,150) if portrait else (96,922,1728,130)
    return ''.join(f'<div id="{prefix}-caption-bg-{i}" class="clip" data-caption-bg="true" data-start="{start:.6f}" data-duration="{end-start:.6f}" data-track-index="4" data-track-kind="captions" style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:#fff;border-radius:13px"></div>' for i,(start,end) in enumerate(windows))
