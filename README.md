# nath-bot
The discord bot that Natherul made with the help from www.soronline.us

If you want to just invite the bot as it is then press the following link:
https://discord.com/oauth2/authorize?client_id=758718771275497559&scope=bot&permissions=268471296

Once invited you need to configure the bot with the relevant information. Get started with issuing "|configure" in any channel the bot can see.

**Support**:

If you need any help which is not a bug please join https://www.guilded.gg/i/1EqWJ75k (no account is needed) and Ill try and help there.

**THIS PART BELOW IS FOR SELFHOSTING ONLY**:

Note that this is only for selfhosting the bot and it will be run as a python script. It comes with two files:

bot.py              <- The actual bot that you will be running.

soronline.py        <- This is used to grab the current state of ingame, the bot runs this periodically.


Remember that you need to edit the first few lines if you are selfhosting this bot or it will not function.


The bot also produces the file results.txt which contains the last information from soronline, this is used on boot up of the bot so that it knows if the current zones are new or not. The bot also prints messages to the screen when it looks for new information and when it posts it to a channel. I would suggest once  implemented to make a simple systemd service out of it and let it turn that output into files.

One such example of a systemd service file is located in the examples folder, this example assumes the scripts are placed in the location: "/home/pi/discBot/".

**Typical usage**:

![normal use](https://github.com/natherul/nath-bot/blob/master/typical.jpg?raw=true)

**Configuring**:

![configure help](https://github.com/natherul/nath-bot/blob/master/configure.jpg?raw=true)

