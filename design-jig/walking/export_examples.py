"""Small comparison boards, all drawn by the candidate native painter."""

import json
from fixtures import fixture
from render import render, Raster
from presentation import compose
from landscapes import STYLES
from concepts import CONCEPTS


def export(root):
    output = root / "renders"
    scenes, concepts = [], []
    for name, title in STYLES:
        item = dict(id=name, title=title)
        for sky in ("gradient", "solid"):
            filename = "scene-%s-%s.png" % (name, sky)
            (output / filename).write_bytes(render(fixture("pending", 500, 0), dict(landscape=name, sky=sky)))
            item[sky] = "./renders/" + filename
        scenes.append(item)
    for name, title, note, draw in CONCEPTS:
        item = dict(id=name, title=title, note=note)
        for state in ("pending", "success"):
            painter = Raster()
            draw(painter, compose(**fixture(state, 500, 0)))
            filename = "concept-%s-%s.png" % (name, state)
            (output / filename).write_bytes(painter.png())
            item[state] = "./renders/" + filename
        concepts.append(item)
    (root / "generated" / "examples.js").write_text("window.walkingExamples=" + json.dumps(dict(scenes=scenes, concepts=concepts)) + ";\n")
