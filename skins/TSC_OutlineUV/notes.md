# TSC_OutlineUV

The user's idea for the outline, as a test (Claude, Opus 5.5, 2026-10-23): "if you paint an outline inside of each
object directly from the parts in UV map, you'll probably see the difference". TSC_OutlineTest's design with each
part's line drawn on its own shape in the map (the distance in the map from its edge's texels, each texel's cm; half
on an edge within 0.5 cm of another part's, the whole elsewhere), nothing measured along the car's surface: the code is
the session's scratch, not the tool's. Deleted once the user has seen it beside TSC_OutlineTest.
- Shown (Claude, Opus 5.5, 2026-10-23): painted in 18 s (the tool's outline 180 s); clean at most places, its edges
  wavy or stepped where the map is stretched, and a seam its parts are 1.7 cm apart at (the deck's back corner,
  (43, 64, -127)) read as two edges: a line twice as wide there.
