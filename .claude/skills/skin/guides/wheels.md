# Wheels: the wheels designer's guide

Read on the studio's car (`studio.md`, 3) when the work reaches the wheels. The user settles the wheels car by car, as one piece of
work ("the wheels in general is a full workflow as I build cars"). It grows with every car: at the
end of the step, add what the car taught under "Learned", dated, with the car's name.

## What good looks like

- **The wheels are a system:** the covers (the big discs seen from the side), the rims and hubs
  behind them, the tyre's sidewall band, the tread, and the wheel ring's light. Design them
  together, from the car's colours.
- **The covers set the stance.** Dark covers ground the car and let the body read; covers in the
  body's colour carry the livery down and lighten it; a bright cover on a dark car shouts.
- **One accent on the tyre ties the car together:** a ring, a stripe or a compound colour from the
  palette (Formula 1's soft, medium and hard rings are the model of a mark that means something).
- **Motion:** the tyres and covers turn. Rings and circles read at speed; spokes and uneven
  graphics blur; words on a tyre read only standing still.
- **The rear tyres are what the player sees most** after the tail: the chase camera sits right
  above them.

## On this car

- The covers are their own paint (`"wheel covers"`), and `"wheels"` is covers, rims, hubs and rings;
  body paint never reaches them. All four wheels and tyres share one paint.
- Tyre markings: the library, `s.tyre_marks("TY-..", colour=, words=, tread=)` (95 of them), and
  treads `s.tyre_tread("TR-..")` (`tool/tyres.py`). A marking lives in a band 4.4 cm wide (30.9 to
  35.3 cm from the axle): lettering caps of 2 to 2.5 cm. The right tyres are the left's mirror:
  words read backwards there unless every letter is B C D E H I K O X 0 3 8 (`SKILL.md`). On the Mac,
  markings with words don't paint (Windows fonts: `IMPROVEMENTS.md`).
- The wheels' lights: the ring glows stock cyan day and night (`s.relight("wheel ring", colour,
  keep_level=True)`); the brake lights inside the front wheels glow at night and flare when braking
  (`s.relight("brake lights", colour)`); the rims glow while braking hard (brake heat); the hubs
  take the turbo pad's colour for about 3 s (the game's colour, not ours).

## Check before showing

- Close looks 8 (the front wheel) and 9 (the driving camera), and the chase cameras.
- At night: the ring and the brake lights in the car's colours, none left stock.
- The marking against the covers' edge and the tread: nothing lost under the cover.

## Learned

- 2026-09-28, TSC_Ladybird: the user picked the grass line (black covers, a thin turf stripe round
  each tyre), the one option that brings the car's idea into the driver's own view. The critic
  flagged the front brake lights' stock orange at night, a colour in no part of the car.
- 2026-09-25, TSC_CMYK_Peel_More: a ring round the wheels must be drawn round the fitted axles
  (`shapes.WHEEL_Y/WHEEL_Z`), or it wobbles as the wheel turns.
