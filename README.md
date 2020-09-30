# nath-bot
The discord bot that Natherul made with the help from www.soronline.us


Note that this is only for selfhosting the bot and it will be run as a python script. It comes with two files:

bot.py              <- The actual bot that you will be running.

soronline.py        <- This is used to grab the current state of ingame, the bot runs this periodically.


Remember that you need to edit the first few lines if you are selfhosting this bot or it will not function.


The bot also produces the file results.txt which contains the last information from soronline, this is used on boot up of the bot so that it knows if the current zones are new or not. The bot also prints messages to the screen when it looks for new information and when it posts it to a channel. I would suggest once  implemented to make a simple systemd service out of it and let it turn that output into files.
