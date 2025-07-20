# fast flag editor for roblox

simple fast flag editor for roblox. nothing special.

## what are fast flags?

roblox uses something called "fast flags" (or `fflags`) to control internal features. most are hidden from users but can enable new stuff, fix performance issues, change behavior, etc.

they're stored in a file called:

`<roblox version>\ClientSettings\ClientAppSettings.json`

you can override them by editing that file. this tool just makes that easier.

## features

- toggle fast flags in a imgui based gui
- search flags
- add/edit/remove flags  
- import/export json configs  
- autosave support  
- detects new roblox versions and carries flags over  

## how it works

this app finds your roblox install inside `localappdata`, loads the json flag file, and lets you view/edit the flags. if roblox updates, it'll try to copy your flags forward so they aren't lost.

## how to run

1. make sure Python 3.10+ is installed

2. install dependencies
`pip install -r requirements.txt`

3. run the program
`python main.py`