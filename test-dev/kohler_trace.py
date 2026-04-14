"""
kohler_illuminator_raytrace.py
──────────────────────────────
2D paraxial ray trace of a Köhler epi-illuminator fed by an integrating sphere.

Layout (all in one focal-unit 'f'):
  Source ──[L1]──────────[L2]──[FS]──[L3]──────[AS]──────[L4]──────[BFP / Objective]
     0      f    f   f   f     f     f   2f     2f   2f   2f

  L1  collector       focal length = f
  L2  first relay     focal length = f   (images source → FS)
  FS  field stop      conjugate with specimen plane
  L3  second relay    focal length = 2f
  AS  aperture stop   conjugate with objective BFP  (in collimated space)
  L4  final relay     focal length = 2f  (images AS → BFP)
  BFP back focal plane of objective

Edit the CONFIG block to change focal lengths, number of rays, colours, etc.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.collections import LineCollection

# ════════════════════════════════════════════════════════════════════════════
# CONFIG  ── edit here ───────────────────────────────────────────────────────
# ════════════════════════════════════════════════════════════════════════════
F          = 50.0   # base focal unit (mm).  All other spacings scale with this.
F_L3_L4    = 2.0    # L3 and L4 focal length as multiple of F
SRC_HALF   = 8.0    # half-height of source port (mm)
N_FIELD    = 7      # number of field points across source height
N_ANGLES   = 8      # number of angle rays per field point
ANGLE_HALF = 0.22   # max launch angle (rad)

DARK_BG    = '#0a0b0c'
AXIS_COL   = '#ffffff'
GRID_COL   = '#1e2022'
LABEL_COL  = '#aaaaaa'
LENS_COL   = '#ccddee'
FS_COL     = '#cc4444'
AS_COL     = '#cc4444'
BFP_COL    = '#4488cc'
OBJ_COL    = '#aaccdd'
RAY_CMAP   = 'plasma'   # matplotlib colormap name for field-point colouring

SAVE_PNG   = True
PNG_PATH   = 'kohler_illuminator.png'
DPI        = 200
# ════════════════════════════════════════════════════════════════════════════

f1 = F
f2 = F
f3 = F_L3_L4 * F
f4 = F_L3_L4 * F

# ── Element x-positions ──────────────────────────────────────────────────────
x_src = 0.0
x_L1  = 1 * F
x_L2  = 3 * F          # source image (at 2f past L1) = FS
x_FS  = 4 * F
x_L3  = 5 * F
x_AS  = x_L3 + 2 * f3
x_L4  = x_AS + 2 * f3
x_BFP = x_L4 + 2 * f4

# ── Thin-lens refraction helper ───────────────────────────────────────────────
def refract_through_lens(y, u, f_lens):
    """Return new angle u' after thin lens at height y."""
    return u - y / f_lens

# ── Ray tracing ───────────────────────────────────────────────────────────────
def trace_ray(y0, u0, lenses):
    """
    Trace a single ray from (x=0, y=y0, angle=u0).
    lenses: list of (x_pos, focal_length | None)
    Returns arrays xs, ys.
    """
    xs = [0.0]
    ys = [y0]
    x, y, u = 0.0, y0, u0
    for x_next, f_next in lenses:
        dx = x_next - x
        y += u * dx
        x = x_next
        xs.append(x)
        ys.append(y)
        if f_next is not None:
            u = refract_through_lens(y, u, f_next)
    return np.array(xs), np.array(ys)

# Lens sequence: (x_position, focal_length or None for free-space waypoints)
lenses = [
    (x_L1, f1),
    (x_L2, f2),
    (x_FS, None),
    (x_L3, f3),
    (x_AS, None),
    (x_L4, f4),
    (x_BFP, None),
    (x_BFP + 18, None),   # run a little past BFP for visual effect
]

field_pts  = np.linspace(-SRC_HALF, SRC_HALF, N_FIELD)
launch_angles = np.linspace(-ANGLE_HALF, ANGLE_HALF, N_ANGLES)
cmap = plt.get_cmap(RAY_CMAP)
fp_colors = cmap(np.linspace(0.15, 0.90, N_FIELD))

all_segs   = []
all_colors = []
for fi, yp in enumerate(field_pts):
    col = fp_colors[fi]
    for a in launch_angles:
        xs, ys = trace_ray(yp, a, lenses)
        # build line-collection segments
        pts = np.column_stack([xs, ys])
        segs = np.stack([pts[:-1], pts[1:]], axis=1)
        for s in segs:
            all_segs.append(s)
            all_colors.append(col)

# ── Figure ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(20, 6))
fig.patch.set_facecolor(DARK_BG)
ax.set_facecolor(DARK_BG)
ax.grid(color=GRID_COL, linewidth=0.4, zorder=0)
ax.axhline(0, color=AXIS_COL, lw=0.5, alpha=0.35, zorder=1)

# ── Rays ──────────────────────────────────────────────────────────────────────
lc = LineCollection(all_segs, colors=all_colors, linewidths=0.55, alpha=0.7, zorder=2)
ax.add_collection(lc)

# ── Source box ───────────────────────────────────────────────────────────────
bw = 18
rect = mpatches.FancyBboxPatch(
    (-bw, -SRC_HALF - 1.5), bw, 2 * (SRC_HALF + 1.5),
    boxstyle='square,pad=0', lw=1.0,
    edgecolor='#6b3d1e', facecolor='#130a04', zorder=3)
ax.add_patch(rect)
for dy in np.linspace(-SRC_HALF + 1.5, SRC_HALF - 1.5, 5):
    ax.plot(-bw + 3, dy, 'o', color='#66ff88', ms=2.8, zorder=5)
ax.text(-bw / 2, SRC_HALF + 3.5, 'Integrating\nsphere port',
        color=LABEL_COL, fontsize=6.5, ha='center', va='bottom',
        fontfamily='monospace')

# ── Lens arrows ───────────────────────────────────────────────────────────────
lens_h = 14
for xL, lbl, f_lbl in [(x_L1,'L1',f'f={f1:.0f}mm'),
                        (x_L2,'L2',f'f={f2:.0f}mm'),
                        (x_L3,'L3',f'f={f3:.0f}mm'),
                        (x_L4,'L4',f'f={f4:.0f}mm')]:
    ax.annotate('', xy=(xL, lens_h), xytext=(xL, -lens_h),
                arrowprops=dict(arrowstyle='<->', color=LENS_COL, lw=1.4), zorder=4)
    ax.text(xL, lens_h + 1.2, lbl,
            color=LENS_COL, fontsize=8, ha='center', va='bottom',
            fontfamily='monospace', fontweight='bold')
    ax.text(xL, -lens_h - 2.5, f_lbl,
            color=LABEL_COL, fontsize=6, ha='center', va='top',
            fontfamily='monospace')

# ── Stop jaws ────────────────────────────────────────────────────────────────
jaw = 4   # gap half-size
for xS, lbl, col in [(x_FS,'FS',FS_COL), (x_AS,'AS',AS_COL)]:
    ax.plot([xS, xS], [ jaw, lens_h + 5], color=col, lw=1.2, zorder=4)
    ax.plot([xS, xS], [-jaw, -lens_h - 5], color=col, lw=1.2, zorder=4)
    for sign in [1, -1]:
        ax.annotate('', xy=(xS, sign*(lens_h+5)),
                    xytext=(xS, sign*(lens_h+8)),
                    arrowprops=dict(arrowstyle='<->', color=col, lw=1.0), zorder=4)
    ax.text(xS, lens_h + 10, lbl,
            color='white', fontsize=10, ha='center', va='bottom',
            fontfamily='monospace', fontweight='bold')

# ── BFP ───────────────────────────────────────────────────────────────────────
ax.axvline(x_BFP, color=BFP_COL, lw=0.9, ls='--', zorder=3)
ax.text(x_BFP, lens_h + 4, 'BFP',
        color=BFP_COL, fontsize=8, ha='center', va='bottom',
        fontfamily='monospace', fontweight='bold')

# ── Objective (trapezoid) ─────────────────────────────────────────────────────
ow = 7; oh_top = 7; oh_bot = 12
ax.fill([x_BFP, x_BFP+ow, x_BFP+ow, x_BFP],
        [-oh_bot, -oh_top, oh_top, oh_bot],
        color='#1a2d3a', zorder=5)
ax.plot([x_BFP, x_BFP+ow, x_BFP+ow, x_BFP, x_BFP],
        [-oh_bot, -oh_top, oh_top, oh_bot, -oh_bot],
        color=OBJ_COL, lw=0.9, zorder=5)
ax.text(x_BFP + ow/2, -oh_bot - 3, 'Objective\nLens',
        color=OBJ_COL, fontsize=6.5, ha='center', va='top',
        fontfamily='monospace')

# ── 45° fold mirror ───────────────────────────────────────────────────────────
mx = x_BFP + 16
ax.plot([mx - 9, mx + 9], [-9, 9], color='#777777', lw=2.0, zorder=5)
ax.text(mx + 11, 3, '45° fold\nmirror', color='#777777',
        fontsize=6, va='center', fontfamily='monospace')

# ── Dimension annotations ─────────────────────────────────────────────────────
y_ann = -lens_h - 16
def dim(x1, x2, lbl):
    ax.annotate('', xy=(x2, y_ann), xytext=(x1, y_ann),
                arrowprops=dict(arrowstyle='<->', color='#555555', lw=0.8))
    ax.text((x1+x2)/2, y_ann - 1.8, lbl, color='#666666', fontsize=6.5,
            ha='center', va='top', fontfamily='monospace')

dim(x_src, x_L1, 'f')
dim(x_L1,  x_L2, '2f')
dim(x_L2,  x_FS, 'f')
dim(x_FS,  x_L3, 'f')
dim(x_L3,  x_AS, '2f')
dim(x_AS,  x_L4, '2f')
dim(x_L4,  x_BFP,'2f')

# ── Conjugate labels ──────────────────────────────────────────────────────────
for xc, txt in [(x_FS, 'image plane\n(field conjugate)'),
                (x_AS, 'pupil plane\n(aperture conjugate)'),
                (x_BFP,'obj. BFP\n(pupil conjugate)')]:
    ax.text(xc, lens_h + 16, txt, color='#778899', fontsize=5.5,
            ha='center', va='bottom', fontfamily='monospace',
            bbox=dict(boxstyle='round,pad=0.3', fc='#111418', ec='#334455', lw=0.6))

# ── Axes ──────────────────────────────────────────────────────────────────────
ax.set_xlim(-bw - 8, x_BFP + 34)
ax.set_ylim(-lens_h - 26, lens_h + 26)
ax.tick_params(colors='#444444', labelsize=6.5)
for sp in ax.spines.values():
    sp.set_edgecolor('#2a2a2a')
ax.set_xlabel('Optical axis  (mm)', color='#555555', fontsize=7.5)
ax.set_title(
    'Köhler Epi-Illuminator — Paraxial Ray Trace   '
    '(integrating sphere → L1→L2→[FS]→L3→[AS]→L4→BFP)',
    color='#cccccc', fontsize=9.5, pad=10)

# ── Legend ────────────────────────────────────────────────────────────────────
legend_elems = [
    mpatches.Patch(color=fp_colors[0],    label=f'Field pt  y={field_pts[0]:.1f} mm'),
    mpatches.Patch(color=fp_colors[N_FIELD//2], label=f'Field pt  y={field_pts[N_FIELD//2]:.1f} mm (axis)'),
    mpatches.Patch(color=fp_colors[-1],   label=f'Field pt  y={field_pts[-1]:.1f} mm'),
    mpatches.Patch(color=LENS_COL,        label='Thin lens'),
    mpatches.Patch(color=FS_COL,          label='FS / AS stop jaw'),
    mpatches.Patch(color=BFP_COL,         label='BFP (aperture conjugate)'),
]
leg = ax.legend(handles=legend_elems, loc='upper left',
                fontsize=6, framealpha=0.35,
                facecolor='#111111', edgecolor='#333333',
                labelcolor='#cccccc')

plt.tight_layout()
if SAVE_PNG:
    plt.savefig(PNG_PATH, dpi=DPI, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    print(f"Saved → {PNG_PATH}")
plt.show()