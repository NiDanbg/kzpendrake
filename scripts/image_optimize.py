"""
Shared image-optimization helper: re-encodes cover images as WebP, targeting
a ~100-200KB file size. Used both by the one-off batch migration
(optimize_covers.py) and by the admin panel's upload endpoint, so newly
uploaded covers get the same treatment automatically.
"""
import io
from PIL import Image

MAX_DIMENSION = 1600          # longest side, px — plenty for a book-cover display size
TARGET_MIN = 100 * 1024       # 100 KB
TARGET_MAX = 200 * 1024       # 200 KB
QUALITY_STEPS = [90, 85, 80, 75, 70, 65, 60, 55, 50, 45, 40, 35, 30]


def _encode(img, quality):
    buf = io.BytesIO()
    img.save(buf, format='WEBP', quality=quality, method=6)
    return buf.getvalue()


def optimize_to_webp(src, max_dimension=MAX_DIMENSION,
                      target_min=TARGET_MIN, target_max=TARGET_MAX):
    """
    src: file path or file-like/bytes object.
    Returns (webp_bytes, quality_used, dimensions).
    Tries decreasing quality until under target_max; if even the lowest
    quality step is still too big, downscales further and retries.
    """
    img = Image.open(src)
    img = img.convert('RGB')

    dim = max_dimension
    while True:
        w, h = img.size
        if max(w, h) > dim:
            scale = dim / max(w, h)
            work = img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
        else:
            work = img

        best = None
        for q in QUALITY_STEPS:
            data = _encode(work, q)
            if len(data) <= target_max:
                best = (data, q)
                if len(data) >= target_min or q == QUALITY_STEPS[-1]:
                    break
        if best is not None:
            return best[0], best[1], work.size

        # Even the lowest quality is too big — shrink dimensions and retry.
        if dim <= 400:
            # Give up shrinking further; return the smallest we managed.
            data = _encode(work, QUALITY_STEPS[-1])
            return data, QUALITY_STEPS[-1], work.size
        dim = int(dim * 0.8)


def optimize_file_to_webp(src_path, dst_path, **kwargs):
    data, quality, size = optimize_to_webp(src_path, **kwargs)
    with open(dst_path, 'wb') as f:
        f.write(data)
    return quality, size, len(data)
