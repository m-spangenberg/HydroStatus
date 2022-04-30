# Start Menu
start_txt = "💧 Welcome to _Hydro Status_\\.\n\
\n\
/auth \\-\\- register device\n\
/help \\-\\- raise the help menu\n\
"

# Help Menu
help_txt = "💧 Thank you for using _Hydro Status_\\. I can return readings \
from your water sensor with the following commands\\.\n\
\n\
*Reporting*\n\
/report \\-\\- text\\, all totals\n\
/graphmonth \\-\\- graph\\, last 4 weeks\n\
\n\
*Information*\n\
/help \\-\\- raises this help menu\n\
/about \\-\\- more help with commands\n\
\n\
"

# About
about_txt = "💧 *About*\n\
\n\
*How To Interact*\n\
To talk to me\\, you have to use commands\\. Simply type a forward slash `/` followed by the command and I will respond\\. \
You can also tap on commands in bright blue if you prefer\\. Commands shown in dark blue will be coppied to your clipboard if you tap on them\\.\n\
\n\
/auth \\-\\- authorizes new users\n\
/help \\-\\- raises the main help menu\n\
/about \\-\\- raises this section\n\
\n\
*Reporting*\n\
The metrics I report are as text and graphs\\. To get graphs that report usage over time\\, simply use the `/graph` command immediately \
followed by either `day`\\, `week`\\, or `month` and a corresponding image will be sent to you\\. To receive your total usage report\\, \
simply use the `/report` command or add a modifier like `hour` for a specific time period\\. See the examples below\\.\n\
\n\
📋 /report \\-\\- all totals\n\
🗒️ /reportnow \\-\\- last minute total\n\
🗒️ /reporthour \\-\\- last hour total\n\
🗒️ /reportday \\-\\- last 24 hours total\n\
🗒️ /reportweek \\-\\- last 7 days total\n\
🗒️ /reportmonth \\-\\- last 4 weeks total\n\
📊 /graphday \\-\\- last 24 hours\n\
📊 /graphweek \\-\\- last 7 days\n\
📊 /graphmonth \\-\\- last 4 weeks\n\
\n\
*Alerts*\n\
By default I will notify you when your water usage exceeds _300L/h_ for longer than 5 minutes\\.\
You can change my threshold and delay by issuing the `/alert` or `/alertdelay` command followed by a value and your hardware key\\. \
The values are in litres per hour and minutes\\, respectively\\. See the examples below\\.\n\
\n\
🚨 min\\: `/alert 180 <key>`\n\
🚨 max\\: `/alert 3000 <key>`\n\
⏳ min\\: `/alertdelay 1 <key>`\n\
⏳ max\\: `/alertdelay 60 <key>`\n\
\n\
*Status*\n\
The status of the entire system is constantly being monitored\\, if I detect a problem anywhere I will use colour\\-coded squares \
to notify you\\. You can see a legend below with each colour and its meaning\\.\n\
\n\
🟩 Functioning\\, System OK\n\
🟧 Minor Issue\\, No Action Needed\n\
🟥 Major Error\\, Needs Attention\n\
"