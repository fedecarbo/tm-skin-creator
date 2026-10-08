# TSC_LinesTest

The road's step 4 (IMPROVEMENTS.md, 2026-10-08, Claude Fable 5.1): a test car for lines laid anywhere on the mesh,
scrapped after the pick. The same design painted twice: A with the tool as it was (the code at 8fe36c3: a picked line
smoothed in the air and pushed back, a line beside a line walked and splined, a line carried on straight through the
air, a drawn line smoothed), B with the lines on the surface itself (the model's chain whole, the straightest way
along the surface between points, a line beside a line as the line where the distance is so many cm, a line carried
on by the surface's straightest way).

- Set 1 (Lines on the mesh · 2 takes): A as it was, B on the surface.
- Shown (2026-10-08, Claude Fable 5.1): set 1 open in the Lab, A (TSC_LinesTest_AsItWas, painted from the old code's
  tree, 8fe36c3) and B (TSC_LinesTest_OnTheSurface). Read back off the body, both takes' bands are whole and even
  along their own lines (the measure can't tell where a line is: step 6's judge); where the lines differ, measured
  in the tool: the picked line down the flank 72.6 cm on the surface against 83.8 by the old code (a zigzag along
  the model's edges, smoothed, up to 11 cm off the straightest way); the old offset round the cockpit's back up to
  8 cm from the line 4 cm beside it; the old drawn line up to 2.9 cm from the straightest way through its points;
  the nose tape's carried-on start within 0.4 cm of the old's, both sides exact mirror images. Close looks of B:
  the block scale runs on over the nose's seam, the cockpit's line is even through its bends, the flank's line
  comes down the roll without steps, the green's edge sits on its line.
- The user (2026-10-08, in the chat, of the set): "Not sure what the green is for, but something I can tell is that
  take A seems a little smoother. And I think the surface, the undersurface is a little jagged, just to let you
  know. Same happens in certain areas. It doesn't mean that take A is better. But certainly there's still a bit of
  blindness. ... I can point you where it's a little jagged from the unsurface. But I can confirm that the on the
  surface works in terms of painting." Read as: B ("On the surface") works but is jagged in places; A's smoothing
  hid it. Measured (Claude Fable 5.1): the distance is read straight across the fine surface's faces, up to 3.6 cm,
  so a line beside a bent line came out as a polygon (a vertex up to 0.35 cm off the line between its neighbours
  on a band's edge along the skirt, 0.22 beside the nose roll). The faces a band's edge or a line beside a line
  bends across are now cut finer and the distance solved again until within half a texel (0.07 after). B repainted;
  the user's pin, where it still looks jagged, is next.
