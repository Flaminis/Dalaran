# Dalaran branding

The Dalaran marks are a small, hand-authored set of SVGs. They are original
artwork made for this repository from geometric primitives only — no upstream
artwork was copied or traced.

## The marks

| File | Use |
| --- | --- |
| [`dalaran-logo.svg`](dalaran-logo.svg) | Square mark. Favicons, avatars, app icons, anywhere the name is already visible. |
| [`dalaran-wordmark.svg`](dalaran-wordmark.svg) | Mark plus the name. READMEs, slide headers, docs navigation. |

The motif is an observatory: an outer dome ring, two crossing ley-line orbits,
and a lens at the centre. It is meant to read as "point the instrument at the
data and actually see it", which is what the project is for.

Both files are hand-written SVG under 1 KB, use no external references, no
embedded raster data, and no gradients or filters, so they scale cleanly and
stay diff-friendly. The wordmark renders its text with a system sans-serif
stack (`Inter` first, falling back to Helvetica/Arial); if you need a mark that
is guaranteed pixel-identical everywhere, export a PNG from the SVG rather than
substituting a different font.

## Palette

| Name | Hex | Role |
| --- | --- | --- |
| Arcane Violet | `#6C4CF1` | Primary. The ring, the lens, the wordmark. |
| Ley Blue | `#2BB8D9` | Secondary. Orbits, links, selection highlights. |
| Rune Gold | `#E8B44A` | Accent. Use sparingly — the lens core, warnings. |
| Void | `#0B0D14` | Dark background. |
| Mist | `#F5F6FA` | Light background. |
| Slate | `#4A5163` | Neutral text and dividers on light backgrounds. |

Arcane Violet and Ley Blue were chosen to keep contrast on both Void and Mist,
so the same single-file mark can be used in dark and light contexts without a
separate variant. Contrast of Arcane Violet on Mist is roughly 6.4:1 and on
Void roughly 4.7:1, which is adequate for large graphical elements; do not use
Arcane Violet for small body text on dark backgrounds.

## Usage rules

Please do:

- use the marks to link to, document, or talk about Dalaran;
- scale them proportionally, and leave clear space of at least half the mark's
  height on every side;
- recolour a mark to a single flat colour (for example all `#F5F6FA`) when you
  need a monochrome version for print or an embroidered patch.

Please do not:

- stretch, rotate, skew, or add drop shadows, glows, or gradients;
- place the mark on a busy photographic background;
- use the marks in a way that implies the Dalaran project endorses, sponsors,
  or maintains your product;
- build a derived product logo that could be mistaken for the Dalaran mark.

If you are unsure whether a use is fine, ask at <opensource@dalaran.dev>. We
would rather answer a short email than send a takedown.

## Licensing

The SVG source files in this directory are licensed under the
[Apache License, Version 2.0](../../LICENSE), like the rest of the repository.
They are additionally offered under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) for use in articles,
talks, and other non-software material, so you do not have to reproduce a
software licence header in a slide deck. Attribution is "Dalaran contributors"
in either case.

Note that the Dalaran *name* is not covered by those licences in the sense that
a licence cannot grant you the right to pass your project off as ours; the
usage rules above apply regardless.
