from frontend.formatting import initials, md_escape
from frontend.theme import PALETTES, build_css


def test_palettes_define_same_variables():
    assert PALETTES["light"].keys() == PALETTES["dark"].keys()


def test_build_css_injects_selected_palette():
    dark = build_css("dark")
    light = build_css("light")
    assert dark.startswith("<style>") and dark.endswith("</style>")
    assert "--bg:#0b1220;" in dark and "--bg:#f8fafc;" in light
    assert "__VARS__" not in dark and "__AVATAR__" not in dark
    assert build_css("nonsense") == light


def test_md_escape_blocks_directives():
    out = md_escape("see :red[x] *now*")
    assert ":red" not in out.replace("\\:", "") and "\\*" in out and "\\[" in out


def test_initials():
    assert initials("Legal Researcher") == "LR"
    assert initials("madonna") == "M"
    assert initials("") == "U"
