Updated: Feb. 18, 2022

# Change Log

This document servers as an overview of MKW Table Bot's releases over time, along with milestones. Many minor updates addressing bugs and text issues were issued between releases, but these are considered the large releases.

## Version 1.0.0
**Released on 08-01-2020**

MKW Table Bot is officially released to the public as a Discord bot to automate making Tables for Mario Kart Wii!

## Version 2.0.0
**Released on 08-07-2020**
- Added commands: ?updates, ?rxx, ?setwarname, ?setprefix (admins only), ?fc, ?stats - see ?help for details
- Bot highly stable, no scorekeeping bugs found. Scorekeeping uses war metadata to shape the room into the table.
- Removed several commands (they've been replaced by better things), thank you to the beta testers!
- Added headers to table pictures to alert people who only recieved the picture if there are errors or not.
- Removed case sensitivity for Lounge names
- ?wp updates the room automatically, no need to do ?ur
- Minor bug fixes
- If you haven't used the bot in the last 2.5 hours, your war will be reset

## Version 2.1.0
**Released on 08-11-2020**
- Advanced tag recognition AI
- ?sw now has a sui format, which will ignore all large times: ?sw 5v5 2 BadWolf sui=yes
- Fixing internal bot error message when starting war before race 1
- Correcting ?wp multi-thread - sorry to those who ran ?wp at the exact same time as another user and got someone else's war picture
- Other minor bug fixes and text clarifications

## Version 3.0.0
**Released on 08-17-2020**
- Added commands: ?penalty, ?teampenalty, ?edit, ?setflag, ?dcs, ?cr, and ?rr
- Improved Tag Recognition AI
- TableBot now officially supports Lounge names (it connects with an API and pulls Lounge data now)

## Version 3.0.1
**Released on 08-20-2020**
- Emergency update to address tag AI crashing bot

## Version 3.1.0
**Released on 08-23-2020**
- Administrative tools added (bot admins now exist with the plethora of bot admin commands)
- Text fixes

## Version 4.0.0
**Released on 08-24-2020**
- Added special locking mechanisms for Lounge, only start wars for yourself in Lounge, Lounge staff can use all commands, bot becomes unlocked automatically after room ends race #12
- (And so Lounge brings in MKW Table Bot)

## Version 4.1.0
**Released on 08-28-2020**
- ?changeroomsize and ?earlydc released

### 09-16-2020
- Bad Wolf takes a break from Discord and development because COVID-19 and development stress greatly impacted his mental health. 

### 10-06-2020
- MKW Table Bot has reached 100,000 commands (and 52,000 table pictures sent)

## Version 5.0.0
**Released on 10-06-2020**
- Bug fixes
- Easier manual tag input - you only have to put in the teams that are incorrect
- Solutions with tags at the front are prioritized, for better tag recognition
- Alpha beta pruning in the tag AI
- New ?vr command

## Version 5.0.1
**Released on 10-06-2020**
- Added limited functionality in certain categories for Lounge

## Version 5.1.0
**Released on 10-23-2020**
- ?changename command added
- ?rtmogiupdate and ?ctmogiupdate commands added for Lounge (no sub support!)

## Version 6.0.0
**Released on 11-19-2020**
- Randomize table colors for 2 teams (instead or Red and Orange)
- Added support for subs in ?rtmogiupdate and ?ctmogiupdate
- ?report for Lounge Reporters - this will make the process much cleaner than the way ?rtmogiupdate currently works
- CT Names for ?vr
- ?removerace command added
- This was intended to be the final release for Table Bot...

## Version 6.0.1
**Released on 11-21-2020**
- Tag AI crashes Table Bot, patch is issued.

## Version 6.0.2
**Released on 01-31-2021**
- More support added for tableupdate commands

### 04-18-2021
- MKW Table Bot has reached 1 million commands, with 500,000 table pictures sent, and is in 600 servers

## Version 6.0.3
**Released on 04-19-2021**
- For Lounge, anyone in the room for a started table can edit the table now

## Version 7.0.0
**Released on 04-03-2021**
- Added ?mii command
- This update revived development for Table Bot
- This command crashed the mii rendering service, so we had to switch to Nintendo's mii rendering service in a minor update

## Version 8.0.0
**Released on 05-09-2021**
- Added ?wws, ?ctwws, ?battles commands

## Version 8.1.0
**Released on 05-17-2021**
- Added ?tabletext command

### 05-19-2021
- TableBot is bug free

## Version 8.2.0
**Released on 05-26-2021**
- Added ?undo command - Table Bot now stores a history
- ?quickedit supports Lounge names now

## Version 9.0.0
**Released on 06-10-2021**
- Added mii heads to the footer of table
- Added ?sw miis=off to turn them off

## Version 9.0.1
**Released on 06-11-2021**
- Disabled ?mii command and removed miis in footer (memory crash)

## Version 9.0.2
**Released on 06-12-2021**
- Fixed memory crash, enabled ?mii command and add miis in footer again

## Version 10.0.0
**Released on 06-13-2021**
- Different table themes can be set (?theme command)
- Different graph settings can be set (?graph command)
- Custom race display size can be set (?size command)
- ?wp byrace added
- ?defaulttheme added, so server admins can set the default table theme for their server
- ?defaultgraph added, so server admins can set the default graph used for tables in their server

### 06-30-2021
- TableBot code is Released on Github

## Version 11.0.0
**Released on 08-04-2021**
- ?defaultpsb added so server admins can set a default for their server if large times should be ignored or not
- ?defaultmiis added so server admins can turn on/off miis in the footer by default for their server
- Display red errors header and display errors for races that have the same finish times
- Display red errors header and display errors for races that have large deltas
- Bring back green header
- Shortened Links (tinyurl) for MKW Lounge mogi updates. Discord locks on iOS when long links are clicked, so this should provide iOS users with a way to load the mmr preview link or admin panel link without locking.

## Version 11.1.0
**Released on 08-06-2021**
- Mid GP subs now supported for mogi updates. Mogi updates can be between 1 and 32 race submissions.
- Documentation updated for table submission help.
- Abuse tracking updated

## Version 11.2.0
**Released on 10-25-2021**
- New tag AI is implemented, which is faster and more accurate in determining correct teams.

## Version 11.3.0
**Released on 11-19-2021**
- Miis on table image are no longer cropped; rather, they are resized to fit.
- Custom track SHA names are fixed.
- Special Grand Star Cup ?wp command.
- Miis pulled multiple at a time instead of one at a time. This fixes issues with miis missing from tables.

## Version 11.4.0
**Released on 12-18-2021**
- Ability to add rewards/bonuses to players via `?penalty` using negative numbers.
- `?redo` command
- Data tracking commands `?populartracks` and `?unpopulartracks` added.

## Version 11.5.0
**Released on 12-27-2021**
- Ability to specify max races for `?wp` and `?tt`
- Bug fixes for `?redo`
- Bug fixes for `?help` not sending because of Discord character limits

## Version 11.6.0
**Released on 01-13-2022**
- Email protected names (Cloudflare protection) now display correctly.
- Patch issued regarding bug where certain Lounge names didn't work for commands.
- New player stat-tracking commands: `?besttracks`, `?worsttracks`, and `?topplayers`.

## Version 11.7.0
**Released on 11-30-2022**
- `?record` command added.

### 02/13/2022
- MKW Table Bot surpasses 1000 servers!

## Version 12.0.0
**Released on 02-14-2022**
- Major dependency change: discord.py -> pycord
- Table Bot supports Discord Components and Interactions.
- Buttons are displayed to confirm and update rooms.
- Table Bot displays error-correcting buttons.
- Table Bot supports Slash commands.
- Using `?dc` directly edits the placements of races.
- `IgnoreLargeTimes` server setting updated to allow for specific format settings, making it much more customizable.
- Command `?copyfrom` allows users to copy a table from another channel to their current channel.

## Version 12.0.1
**Released on 02-15-2022**
- Help command redirects to GitHub Wiki page.
- `?flags` command, which displays a list of available table flags.
- `?page` command, which shows players' recent Wiimmfi rooms.
- Bug fix for when races were removed after suggestions had been sent. Suggestion buttons now refresh themselves after race removals and table state changes.
- Various small bugs resolved.

## Version 12.1.0
**Released on 02-20-2022**
- If users do not have a flag set with Table Bot, flags are automatically added to the tables based on the user's mii location data.
- Command tracker is added.
- Table updates automatically on room load.
- Patch issued for bug when a button receives more than one interaction at the same time.

## Version 12.1.1
**Released on 02-21-2022**
- Manual DC placements and placement changes were being applied separately, causing an error where Table Bot would try to edit a placement that no longer existed; patch is issued.

## Version 13.0.0
**Released on TBD**
- TableBot changes from HTML parsing to mkwx JSON, updating itself every 10 seconds, and forms a picture of rooms and times.
- Paves way for faster ?wp commands since ?wp no longer pings mkwx. Paves way for automatic table updating and allows rooms to be started before the first race finishes.
