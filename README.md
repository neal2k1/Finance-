# Finance-
Basic Finance WebApp allows user to buy and sell shares with Realtime prices

usage
To get an API_KEY to run your own flask sign up to 
https://iexcloud.io/cloud-login?r=https%3A%2F%2Fiexcloud.io%2Fconsole%2F#/register
then run on the command-line:

for mac and linux

cd [path to app.py]
export API_KEY=[your api key]
export FLASK_APP=app.py
flask run

optional
export FLASK_ENV=development
export FLASK_DEBUG=1

for Windows
cd [path to app.py]
set API_KEY=[your api key]
set FLASK_APP=app
flask run

optional
set FLASK_ENV=development
set FLASK_DEBUG=1
for more info visit: https://flask.palletsprojects.com/en/1.0.x/cli/

