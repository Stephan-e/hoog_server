import datetime, json
from flask import Flask, render_template, request, redirect, Markup, make_response, url_for
from lib.cors import crossdomain
from lib.setup import rooms, settings
from lib.GPIOSetup import GPIO
from lib.appliance import ApplianceObject
from lib import authentication
app = Flask(__name__)


def updateStates(rooms):
	for i, room in enumerate(rooms):
		for j, Appliance in enumerate(room['Controls']):
			current_Appliance = ApplianceObject(Appliance)
			rooms[i]['Controls'][j]['State'] = current_Appliance.getState()
	return rooms

@app.context_processor
def inject_enumerate():
    return dict(enumerate=enumerate)


@app.route("/")
@authentication.login_required
def main():
	now = datetime.datetime.now()
	timeString = now.strftime("%Y-%m-%d %I:%M %p")
	templateData = {
		'title' : 'WebGPIO',
		'time': timeString,
		'rooms' : updateStates(rooms),
		'refresh_rate' : settings['RefreshRate']*1000
	}
	return render_template('main.html', **templateData)

@app.route("/grid/")
@authentication.login_required
@crossdomain(origin='*')
def grid():
	templateData = {
		'title' : 'WebGPIO',
		'rooms' : updateStates(rooms)
	}
	return render_template('grid.html', **templateData)

@app.route("/button/<int:roomNumber>/<int:accNumber>/")
@authentication.login_required
@crossdomain(origin='*')
def button(roomNumber, accNumber):
	current_Appliance = ApplianceObject(rooms[roomNumber]['Controls'][accNumber])
	current_Appliance.executeAction()
	templateData = {
		'title' : 'WebGPIO',
		'state' : current_Appliance.getState(),
		'roomNumber' : roomNumber,
		'accNumber' : accNumber,
		'name' : current_Appliance.name
	}
	return render_template('button.html', **templateData)

@app.route("/login/")
def login():
	return render_template('login.html')

@app.route("/authenticate/", methods=['GET', 'POST'])
def auth():
	if request.method == 'POST':
		password = request.form['password']
		token = authentication.generateToken(password)
		if token:
			expiry_date = datetime.datetime.now() + datetime.timedelta(days=30)
			response = make_response(redirect(url_for('.main')))
			response.set_cookie('token', token, expires=expiry_date)
			return response
	return redirect(url_for('.login'))

@app.route("/logout/")
def logout():
	authentication.removeToken()
	response = make_response(redirect(url_for('.login')))
	response.set_cookie('token', '', expires=0)
	return response

if __name__ == "__main__":
	if settings['SSL']['Enabled']:
		app.run(host = settings['Host'], 
				port = settings['Port'], 
				threaded = settings['Threaded'], 
				debug = settings['Debug'], 
				ssl_context = (settings['cerPath'], settings['keyPath']))
	else:
		app.run(host = settings['Host'], 
				port = settings['Port'], 
				threaded = settings['Threaded'], 
				debug = settings['Debug'])