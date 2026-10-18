# The Mac app: the Lab and Claude in one window

One window: the Lab on the left (the same page the browser shows, from the Lab's server), the real
Claude Code on the right, in a terminal, already in the repo. Claude runs with the user's own
claude.ai sign-in, skills, rules, hooks and memory, exactly as in any terminal. The app starts the
Lab's server the way `tool/doctor.py` does when nothing answers, and leaves it running on quit.

It doesn't bundle the tool's Python: it uses the work folder already set up on this Mac
(`.claude/rules/tool.md`, "Set up a fresh clone"). It needs the Claude Code command line
(`curl -fsSL https://claude.ai/install.sh | bash`, which keeps itself updated).

## Build

From `app/`, with Node 24: `npm install`, then `npm run build`. The app is
`dist/mac-arm64/Skin Lab.app`; copy it to Applications. On the first start it asks for the repo
folder when it isn't beside `app/` (remembered in `~/Library/Application Support/Skin Lab/`).

`npm start` runs it from the checkout. From a VS Code terminal, run it as
`env -u ELECTRON_RUN_AS_NODE npm start`: VS Code sets that variable, and it makes Electron run as
plain Node.

## Check

`SKIN_LAB_SHOT=/tmp/lab.png "dist/mac-arm64/Skin Lab.app/Contents/MacOS/Skin Lab"` saves a picture
of the window after 30 s: the car and the chat on the left, Claude's prompt on the right. A `claude`
process sits under the app's process while it runs (`ps -axo pid,ppid,command | grep claude`).

## The pieces

Electron, xterm with its fit addon, node-pty (compiled for Electron by `electron-builder
install-app-deps` on `npm install`), electron-builder for the `.app`, unsigned (it's for this Mac).
