# MKW-Table-Bot
MKW Table Bot is a Discord Bot created by Bad Wolf to automatically create tables for online rooms in Mario Kart Wii. It also played a part in transforming the way Lounge updates rating to a more automated process. MKW Table Bot also provides many other smaller tools for people.  A full documentation of everything TableBot does can be found below.

## What Can Table Bot Do?
Visit the Documentation to see all the commands: https://github.com/BadWolf1023/MKW-Table-Bot/wiki

## Get Started

[**Invite the Bot**](https://discord.com/api/oauth2/authorize?client_id=1019051989734273054&permissions=124992&scope=applications.commands%20bot)

[**Join the Table Bot Discord Server**]( https://discord.gg/K937DqM)


## Credits: 
* Bad Wolf#1023 (Creator)
* andrew#9232
* camelwater#6035
* liam#8547
  

# Developers, READ BELOW
You will need to set up a few things before you can actually run the code. Even after you have set up a few things, some features will be limited. Below is a guide on how to set up the bot, useful information, and the limitations of running it in your testing enviornment:

**Setup:**
1. To run a Discord bot in general, you need to have a developer account and obtain a bot token. For instructions on how to do so, please refer to here: https://discordpy.readthedocs.io/en/stable/discord.html
2. Make a copy of `private_example.txt`. Name it `private.txt`.
3. Put the bot token in the appropriate places in `private.txt`.
4. Install all dependencies in `Dependencies.txt`. Consider using `pip install` to do so. Note: there is a Node.js dependency. You will need to install Node.js and install this dependency. (No, we don't write Node.js code, it's just used for the localtunnel.)
5. You can run now the bot by running `BadWolfBot.py`

**Limitations:**
1. You cannot actually make requests to Wiimmfi to pull room data. Wiimmfi is protected with Cloudeflare. Our server has been whitelisted, but your computer is obviously not whitelisted. Therefore, to test, use one of our testing rooms, which can be accessed with special rxx numbers when you start the table. Eg `sw 2v2 6 r0000001` (Or you can create more testing rooms in the `testing_rooms` folder and update this line of code: https://github.com/BadWolf1023/MKW-Table-Bot/blob/main/WiimmfiSiteFunctions.py#L60C1-L60C20 )
2. You may or may not have an API key for 255mp's API. You can reach out to him for a key, but you generally don't need it. It's simply used to pull player names based on their discord ID or FC. Without it, their mii name will be displayed (rather than their Lounge name). Not a huge issue!

**Useful information (navigating the project, squashing bugs and project oddities):**
- Some exceptions are logged in `logfile.log` and aren't displayed in the console. We will probably change this in the future, but for now, you'll need to actively check this file for raised exceptions.
- `BadWolfBot.py` is the main file. This is what you run to start the bot.
- The Slash command interfaces are in the `slash_cogs` folder. When a slash command is sent, Table Bot transforms it into a text command and then sends it over to `BadWolfBot.py`.
- If a text command is sent, it comes directly to `BadWolfBot.py`
- In short, if you are not modifying the slash command interface for a command, just jump to the area in `BadWolfBot.py` where the command is processed and start following the rabbit trail.
- A good IDE is recommended! It will help you jump around the project and save time.
  - New to developing? Check out [Pycharm](https://www.jetbrains.com/pycharm/) - since this is an OSS project, you can download the Community Edition for free.
