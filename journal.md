---
title: "t-emu (working title eek)"
author: "Jace Leuthardt"
description: "I wasn't a big fan other other terminal emulators, so I made one myself"
created_at: "2026-03-16"
---

# Retroactive preface:
the journal guide just came out today so that's why so much time is getting skipped

as much as i've tried to like other terminal emulators, there's just been something missing from each one that put me off of it. most of it being that they all want big config files that you have to manually edit.

so my idea is kinda like; an actually good simple config gui in a terminal emulator that won't piss you off to use. a mix of normal app modernity with the utility of the terminal, in something that isn't trying to be entirely AI or something (warp terminal...)

i'm going to include an AI thing, but i'm writing it the right way imo, as in, fully out of the way unless you deliberately invoke it. not even a tooltip telling you "ctrl+whatever to ask AI" or something. and it can be fully disabled ENTIRELY. by entirely, i mean no toolips, no grayed out spots in the sidebar, no nothing. the only remnant will be the switch to turn it back on.

i'm not necessarily making this to appeal to the masses, moreso people like me, a power user, that is allowed to just do their thing, without losing the modern help that apps give you. i don't wanna spend an hour on a dotfile, i wanna do the thing i'm trying to do in a way that still feels like home for me.

that's kinda why i keep coming back to Konsole, it's not that compliated and it always works how I need it to, there's just things I'd like to add to it.

it's not gonna be perfect for everyone, that's the point.


# 20 Mar: getting there

so far today i've gotten resizing the terminal working. i mean, it worked before, but interactive apps didn't respond. now they're responsive so things like htop work well

i also got special keys working, so F-keys and key combos will work now.

i got a suggestion from someone on slack to add command completion. i think i'd just base it off ```history``` but not a bad idea. i'm not a big fan of command completion but it's easy enough to toggle on/off

i'm currently trying to get ctrl+c, and arrow keys working, but i'm having a hard time. i have work soon and can't work more today on the project, so total time about 1h 15m. we'll figure it out tho :3