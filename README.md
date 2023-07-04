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

1.To run a Discord bot in general, you need to have a deveoper account and obtain a bot token. For instructions on how to do so, please refer to here: https://discordpy.readthedocs.io/en/stable/discord.html
2. Make a copy of `example_private.txt`. Name it `private.txt`.
3. Put the bot token in the appropriate places in `private.txt`.
4. Install all dependencies in `Dependencies.txt`. Consider using `pip install` to do so. Note: there is a Node.js dependency. You will need to install Node.js and install this dependency. (No, we don't write Node.js code, it's just used for the localtunnel.)
5. You can run the bot by running `BadWolfBot.py.

Please note the following limitations:
1. You cannot actually make requests to Wiimmfi to pull room data. Wiimmfi is protected with Cloudeflare. Our server has been whitelisted, but your computer is obviously not whitelisted. Therefore, to test, use one of our testing rooms, which can be accessed with special rxx numbers when you start the table. Eg `sw 2v2 6 r0000001` (Or you can create more testing rooms in the `testing_rooms` folder and update this line of code: https://github.com/BadWolf1023/MKW-Table-Bot/blob/main/WiimmfiSiteFunctions.py#L60C1-L60C20 )
2. 
