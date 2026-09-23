# Trackmania Skin Challenge

## What I want

A tool that makes paint jobs (skins) for the car in Trackmania 2020: the default
stadium car, which the game calls CarSport.

## Who I am

I'm not technical. I won't read code, and I won't read or edit the files the tool uses
to describe a design. You make every technical decision. Ask me only what only I can
answer: what I want the skin to look like, and whether I like what you show me.

## My side of it

1. I describe a skin to you in a chat, in my own words.
2. You show me pictures of it on the car.
3. I tell you what to change, or I say yes.
4. When I say yes, the skin is in my game and I can select it.

## How I'll judge it

- **I like the skin, in the game.** A skin I would actually drive with, not only one
  that looks good in a picture.
- **It's fast.** From my words to the car in minutes, not hours.
- **It's all in words.** I never open a paint program or touch a file.
- **It stays small and simple.** I'd rather have less machinery than more.

How you build it is up to you.

## Checkpoints

Don't try to build the whole thing in one session. Your first job is a plan: break the
work into checkpoints and write them down as a checklist file in the repo. Before any
building starts, I'll look at it with you.

For each checkpoint:

- **What it's for**, in plain words I can follow.
- **What I'll see when it's done:** something I can look at or try, so I know it worked.
- **Which Claude model to use**, and why: a big model for the hard thinking, a
  smaller, faster one for straightforward work.

A new session starts cold. It should be able to open the checklist, find the next
checkpoint and carry on, without me explaining anything again. Tick a checkpoint off
only when I've seen what it promised. If what we learn changes the plan, update the
checklist.

## My machine

- Windows. The game is installed through Steam.
- The game loads skins from `Documents\Trackmania\Skins\Models\CarSport\`. On this PC,
  Documents is inside OneDrive:
  `C:\Users\fedec\OneDrive\Documents\Trackmania\Skins\Models\CarSport\`.

## What I'm giving you

The `official/` folder has the files you can't make yourself:

- `CarSport-Template.zip`: Nadeo's skin template, with their instructions and the flat
  UV maps of the car.
- `CarSport-Model.zip`: the car's 3D model, with its unpainted textures.

`official/SOURCES.md` says where each came from, and links Nadeo's published pages
about skins. Everything else is yours to find, choose or build.
