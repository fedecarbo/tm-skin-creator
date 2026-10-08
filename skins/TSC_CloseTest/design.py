"""A throwaway test car for the close looks' diff (the road's step 7): deleted after."""
import numpy as np

SHOULDER = (64, 61, -84)


def design(s):
    from tool import marks, meshlines
    s.clay()
    s.step("Base", "The body in one pale colour.")
    s.paint("body", "satin", colour="#d9d6cf")
    s.step("Stripe", "A red strip along the rear flank's shoulder.")
    shoulder = meshlines.line(SHOULDER, kind="rounded").between(-56, -76)
    s.paint("body", "satin", colour="#1f5fd0", zone=shoulder.strip(0.8))
    s.step("Badge", "A black disc just under the strip's front end.")
    at = tuple(meshlines._closest(shoulder.pts[0] + np.array([2.0, -6.0, 0.0]))[1])
    s.mark("body", "satin", marks.disc(), size=5, at=at, colour="#141414", across=True)
