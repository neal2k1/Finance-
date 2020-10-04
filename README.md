# Finance-
Basic Finance WebApp allows user to buy and sell shares with Realtime prices <br>

# usage <br>
To get an API_KEY to run your own flask sign up to 
https://iexcloud.io/cloud-login?r=https%3A%2F%2Fiexcloud.io%2Fconsole%2F#/register <br>
then run on the command-line:

## for mac and linux

cd [path to app.py] <br>
export API_KEY=[your api key] <br>
export FLASK_APP=app.py <br>
flask run <br>

### optional <br>
export FLASK_ENV=development  <br>
export FLASK_DEBUG=1 <br>

## for Windows
cd [path to app.py] <br>
set API_KEY=[your api key] <br>
set FLASK_APP=app <br>
flask run <br>

### optional
set FLASK_ENV=development <br>
set FLASK_DEBUG=1 <br>
for more info visit: https://flask.palletsprojects.com/en/1.0.x/cli/ <br>

