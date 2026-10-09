"""TSC_WearTest: the road's step 11, wear where real cars wear: a test car, scrapped after the pick."""
from tool import shapes


def design(s):
    s.clay()
    s.step("The livery", "Gloss blue over a light primer, the lower body red.",
           words="wear where real cars wear (the road's step 11)")
    s.paint("body", "satin", colour="#d9d4c7")  # the primer: what the wear shows through
    under = s.keep()
    s.paint("body", "gloss", colour="#1f4fa8")
    s.paint("body", "gloss", colour="#c8102e", zone=shapes.below(30))
    s.paint("inner", "satin", colour="#2b2d31")
    s.paint("wheels", "satin", colour="#2b2d31")
    s.step("Wear", "The paint aged: faded, chipped, scraped, the clear coat gone in places, grime in its corners.")
    s.wear(under, fade=0.25, chips=0.4, scrapes=0.6, clearcoat=0.08, grime=0.6)
