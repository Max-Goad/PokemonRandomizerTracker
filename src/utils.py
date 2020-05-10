import colorsys
import itertools
import pathlib

def resource(path):
    root_dir = pathlib.Path()
    while not (root_dir / ".git").exists():
        root_dir = root_dir.parent
    return root_dir.resolve() / "resources" / path

def flatten(l):
    return list(itertools.chain(*l))

def halve(l):
    half = len(l)//2
    return l[:half], l[half:]

def rgb_to_hex(r, g, b):
    """Converts from three rgb
    numbers to their hex representations.
    """
    assert (0.0 <= r <= 1.0) and (0.0 <= g <= 1.0) and (0.0 <= b <= 1.0), f"OOB:[{r}, {g}, {b}]"
    return "{0:02x}{1:02x}{2:02x}".format(int(r*255),int(g*255),int(b*255))

def hsv_to_hex(h, s, v):
    """Convert from three hsv
    numbers to their hex representations.
    """
    assert (0.0 <= h <= 1.0) and (0.0 <= s <= 1.0) and (0.0 <= v <= 1.0),  f"OOB:[{h}, {s}, {v}]"
    return rgb_to_hex(*colorsys.hsv_to_rgb(h, s, v))