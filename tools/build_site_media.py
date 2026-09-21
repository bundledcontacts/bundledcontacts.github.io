#!/usr/bin/env python3
"""Regenerate every video and figure the project page shows.

The cuts are not re-invented here.  This script imports the ICRA video build
(`../BCG-Paper/Videos/build/`) and calls its own `part_clip` / `join`, so the
hardware footage on the page is clipped, ordered and cross-faded exactly as it
is in the film -- edit `timeline.py` and both follow.

    python3 tools/build_site_media.py             # everything
    python3 tools/build_site_media.py hero grad    # only those groups

Groups: hero, deploy, sim2sim, grad, stills, pipeline, mainfig
"""
import os
import re
import shutil
import subprocess
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
VIDEOS = os.path.normpath(os.path.join(SITE, "..", "Videos"))
BUILD = os.path.join(VIDEOS, "build")
PAPER = os.path.normpath(os.path.join(SITE, ".."))

VID_OUT = os.path.join(SITE, "static", "videos")
IMG_OUT = os.path.join(SITE, "static", "images")

sys.path.insert(0, BUILD)
import build_video as B                                       # noqa: E402
import timeline as T                                          # noqa: E402

TMP = os.path.join(B.WORK, "site")


# --------------------------------------------------------------------------
# encoding
# --------------------------------------------------------------------------
def web(src, out, height=720, crf=27, fps=30, audio=False):
    """Re-encode one finished cut for the web: capped height, faststart, and
    BT.709 tags (see COLOUR in build_video.py -- the iPhone sources are tagged
    HLG and browsers wash them out otherwise)."""
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", src,
           "-vf", f"scale=-2:{height}:flags=lanczos,fps={fps},format=yuv420p",
           "-c:v", "libx264", "-crf", str(crf), "-preset", "slow",
           "-pix_fmt", "yuv420p", *B.COLOUR, "-movflags", "+faststart"]
    cmd += (["-c:a", "aac", "-b:a", "128k"] if audio else ["-an"])
    B.sh(cmd + [os.path.join(VID_OUT, out)])
    p = os.path.join(VID_OUT, out)
    print(f"  {out:34s} {os.path.getsize(p)/1e6:5.1f} MB  {B.duration(p):5.1f}s")


def poster(src, out, at, width=1280):
    B.sh(["ffmpeg", "-y", "-v", "error", "-ss", f"{at}", "-i", src,
          "-frames:v", "1", "-vf", f"scale={width}:-2", "-q:v", "3",
          os.path.join(IMG_OUT, out)])
    print(f"  {out:34s} {os.path.getsize(os.path.join(IMG_OUT, out))/1e3:5.0f} kB")


def cut(parts, name, xfade=0.0):
    """Trim + join a list of timeline parts with build_video's own functions."""
    pieces = [B.part_clip(p, os.path.join(TMP, f"{name}_{i}.mp4"))
              for i, p in enumerate(parts)]
    return B.join(pieces, os.path.join(TMP, f"{name}.mp4"), xfade)


# --------------------------------------------------------------------------
# which timeline segments are hardware footage
# --------------------------------------------------------------------------
def deployment_segments():
    """[(name, parts, xfade)] for every segment shot on the real robot, in the
    order the film plays them.  Derived from timeline.py, never hardcoded."""
    out = []
    for seg in T.SEGMENTS:
        if seg["kind"] == "title" and seg["src"].startswith("Deployment/"):
            out.append(("intro",
                        [dict(src=seg["src"], t0=seg["t0"], t1=seg["t1"])], 0.0))
        elif seg["kind"] == "clip" and all(
                p["src"].startswith("Deployment/") for p in seg["parts"]):
            out.append((seg["key"].split("_")[-1],
                        [dict(p) for p in seg["parts"]], seg.get("xfade", 0.0)))
    return out


# --------------------------------------------------------------------------
# groups
# --------------------------------------------------------------------------
def g_hero():
    """One long loop of every hardware shot, cross-faded as in the film.  No
    title card and no burnt-in motion captions -- the page's own title sits on
    top of it."""
    parts = [p for _, ps, _ in deployment_segments() for p in ps]
    src = cut(parts, "hero", T.XFADE)
    web(src, "hero_deployment.mp4", height=720, crf=28)
    poster(src, "hero_poster.jpg", 2.0)


def g_deploy():
    """The four hardware motions, one clip each, cut exactly as segments 11-14."""
    for name, parts, xf in deployment_segments():
        if name == "intro":
            continue
        web(cut(parts, f"deploy_{name}", xf), f"real_{name}.mp4",
            height=540, crf=28)


def g_sim2sim():
    """Sim-to-sim: the policies replayed in MuJoCo, full clips."""
    for seg in T.SEGMENTS:
        if seg["key"] != "10_sim2sim":
            continue
        for part in seg["parts"]:
            name = os.path.basename(part["src"]).replace("_sim2sim.mp4", "")
            web(os.path.join(VIDEOS, part["src"]), f"sim2sim_{name}.mp4",
                height=540, crf=28)


def g_grad():
    """The three gradient visualisations: forward rollout, then the backward
    pass sweeping back through the same rollout."""
    web(os.path.join(VIDEOS, "4_gradient_variance_soft_stiff/gradients_soft.mp4"),
        "grad_soft.mp4", height=540, crf=28)
    web(os.path.join(VIDEOS, "4_gradient_variance_soft_stiff/gradients_stiff.mp4"),
        "grad_stiff.mp4", height=540, crf=28)
    for seg in T.SEGMENTS:
        if seg["key"] == "06_bcg":
            web(cut(seg["parts"], "grad_bundled", seg.get("xfade", 0.0)),
                "grad_bundled.mp4", height=540, crf=28)


def g_stills():
    """Soft-vs-stiff penetration: the film's split-screen, full body and the
    foot close-up where the red wedge under the soft foot is visible."""
    pen = os.path.join(VIDEOS, "8_penetration_comparison/soft_vs_stiff.mp4")
    for out, at in (("penetration_body.jpg", 2.0), ("penetration_foot.jpg", 9.0)):
        poster(pen, out, at, width=1400)
    web(pen, "penetration_compare.mp4", height=540, crf=28)


def g_pipeline():
    """One panel per pipeline stage, framed by that stage's camera rect -- the
    stills behind the slideshow in the long cut of the film."""
    stages = next(s for s in T.SEGMENTS if s["key"] == "07_pipeline")["stages"]
    pngs = B.render_stage_pngs(stages)
    # A stage with no narration exists only so an element appears mid-sentence;
    # on a page it has no text of its own, so it folds into the stage before it
    # and contributes its (later) picture.
    panels = []
    for png, st in zip(pngs, stages):
        if st.get("say") is None and panels:
            panels[-1] = (png, st, panels[-1][2])
        else:
            panels.append((png, st, st["say"]))
    aspect = 1816 / 948                       # the film's slide, kept identical
    for k, (png, st, _say) in enumerate(panels):
        img = Image.open(png).convert("RGB")
        fw, fh = img.size
        x0, y0, x1, y1 = st["cam"]
        cx, cy = (x0 + x1) / 2 * fw, (y0 + y1) / 2 * fh
        w, h = (x1 - x0) * fw, (y1 - y0) * fh
        w, h = (h * aspect, h) if w / h < aspect else (w, w / aspect)
        box = (round(cx - w / 2), round(cy - h / 2),
               round(cx + w / 2), round(cy + h / 2))
        out = Image.new("RGB", (box[2] - box[0], box[3] - box[1]), (255, 255, 255))
        sx0, sy0, sx1, sy1 = max(0, box[0]), max(0, box[1]), min(fw, box[2]), min(fh, box[3])
        if sx1 > sx0 and sy1 > sy0:
            out.paste(img.crop((sx0, sy0, sx1, sy1)), (sx0 - box[0], sy0 - box[1]))
        W = 1500
        out.resize((W, round(W / aspect)), Image.LANCZOS).save(
            os.path.join(IMG_OUT, f"pipeline_{k}.png"), optimize=True)
        print(f"  pipeline_{k}.png")


def g_mainfig():
    """The paper's first-page figure."""
    pdf = os.path.join(PAPER, "main-fig", "main-fig.pdf")
    stem = os.path.join(TMP, "main_fig")
    W = 1500
    # render at the dpi that lands on W natively -- never upscale a vector figure
    r = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True)
    pts = float(re.search(r"Page size:\s+([\d.]+)", r.stdout).group(1))
    B.sh(["pdftoppm", "-png", "-r", f"{W / pts * 72:.0f}", "-singlefile", pdf, stem])
    img = Image.open(stem + ".png").convert("RGB")
    img.save(os.path.join(IMG_OUT, "main_fig.png"), optimize=True)
    print(f"  main_fig.png  {img.size}")


GROUPS = dict(hero=g_hero, deploy=g_deploy, sim2sim=g_sim2sim, grad=g_grad,
              stills=g_stills, pipeline=g_pipeline, mainfig=g_mainfig)


def main():
    want = sys.argv[1:] or list(GROUPS)
    for d in (TMP, VID_OUT, IMG_OUT):
        os.makedirs(d, exist_ok=True)
    for name in want:
        print(f"--- {name}")
        GROUPS[name]()
    shutil.rmtree(TMP, ignore_errors=True)


if __name__ == "__main__":
    main()
