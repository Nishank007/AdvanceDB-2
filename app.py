"""Cloud Foundry test"""
from flask import Flask, render_template, request, redirect, url_for
import os, datetime
import sqlite3
import math

app = Flask(__name__)

print(os.getenv("PORT"))
port = int(os.getenv("PORT", 5000))

conn = sqlite3.connect('earthquake.db', check_same_thread=False)
connection = sqlite3.connect('all_month.db', check_same_thread=False)

print("Opened database successfully")


# default
@app.route('/', methods=["GET"])
def index():
	result = {}
	return render_template('index.html', result=result)


@app.route('/query1', methods=["POST"])
def problem_1():
	magnitude = request.form["magnitude"]
	cur = connection.cursor()
	cur.execute("""SELECT id, place, mag, REPLACE(REPLACE(time, 'Z', ' '), 'T', ' '), latitude, longitude, depth
	from all_month where mag >= ?""", (magnitude,))
	result = cur.fetchall()
	return render_template('prob1.html', len=len(result), result=result)

# @app.route('/probquery', methods=["POST"])
# def probquery():
# 	mag = request.form["mag"]
# 	cur = conn.cursor()
# 	sql="SELECT * FROM quakes WHERE mag >= ?;"
# 	cur.execute(sql,(mag, ))
# 	result = cur.fetchall()
# 	return render_template('prob1.html', result = result)

# Search for 2.0 to 2.5, 2.5 to 3.0, etc magnitude quakes 
# for a one week, a range of days or the whole 30 days.
@app.route('/query2', methods=["POST"])
def problem_2():
	start_magnitude = request.form["start_magnitude"]
	end_magnitude = request.form["end_magnitude"]
	if start_magnitude > end_magnitude:
		return "start magnitude greater than end magnitude"
	cur = connection.cursor()
	if request.form["dates"] == "all":
		cur.execute("""SELECT * from all_month where mag between (?) and (?)""", (start_magnitude, end_magnitude,))
		result = cur.fetchall()
	elif request.form["dates"] == "date":
		start_range = datetime.datetime.strptime(request.form["start_range"], "%Y-%m-%d").replace(hour=0,
		minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
		end_range = datetime.datetime.strptime(request.form["end_range"], "%Y-%m-%d").replace(hour=23,
		minute=59, second=59, microsecond=999999).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

		if start_range is None:
			return "start date required"
		if end_range is None:
			return "end date required"
		if start_range > end_range:
			return "start date greater than end date"
		cur.execute("""SELECT id, REPLACE(REPLACE(time, 'Z', ' '), 'T', ' '), mag, latitude, longitude, depth, place
		from all_month where mag between (?) and (?) and REPLACE(REPLACE(time, 'Z', ' '), 'T', ' ') 
		between (?) and (?)""", (start_magnitude, end_magnitude, start_range, end_range,))
		result = cur.fetchall()
	else:
		result = []
	return render_template('prob2.html', result=result)


# Search for and count all earthquakes that occurred
# with a magnitude greater than 5.0
@app.route('/querymagp', methods=["POST"])
def problem_mag_point():
	st_mag = float(request.form["start_magnitude"])
	end_mag = float(request.form["end_magnitude"])
	if st_mag > end_mag:
		return "start magnitude greater than end magnitude"
	cur = connection.cursor()
	ret = {}
	while st_mag < end_mag:
		cur.execute("""SELECT * from all_month where mag between (?) and (?)""", (st_mag, st_mag + 0.1))
		result = cur.fetchall()
		ret["Magnitude " + str(round(st_mag, 1)) + " to " + str(round(st_mag + 0.1, 1)) + ", " +
			str(len(result)) + " earthquakes"] = result
		st_mag = st_mag + 0.1
		st_mag = round(st_mag, 1)

	return render_template('magpointinc.html', result=ret)


# earth quakes that were near 20 km or some Km from a specified location
@app.route('/query3', methods=["POST"])
def problem_3():
	latitude = float(request.form["latitude"])
	longitude = float(request.form["longitude"])
	distance = float(request.form["distance"])
	cur = connection.cursor()
	cur.execute("""SELECT id, place, mag, time, latitude, longitude, depth from all_month""", ())
	result = cur.fetchall()
	i = 0
	result1 = []
	for row in result:
		distance1 = round((((math.acos(math.sin((latitude*(22/7)/180)) *
								math.sin((float(row[4])*(22/7)/180))+math.cos((latitude*(22/7)/180)) *
								math.cos((float(row[4])*(22/7)/180)) *
								math.cos(((longitude - float(row[5]))*(22/7)/180))))*180/(22/7))*60*1.1515*1.609344),2)
		result[i] += (distance1,)
		if distance1 <= distance:
			result1.append(result[i])
		i += 1
	return render_template('prob3.html', result=result1)


# find clusters of earth quake
@app.route('/query4', methods=["POST"])
def problem_4():
	start_latitude = float(request.form["start_latitude"])
	start_longitude = float(request.form["start_longitude"])

	end_latitude = float(request.form["end_latitude"])
	end_longitude = float(request.form["end_longitude"])

	step = float(request.form["step"])

	if start_latitude > 90 or start_latitude < -90:
		return "start latitude out of bounds"
	if end_latitude > 90 or end_latitude < -90:
		return "end latitude out of bounds"
	if start_longitude > 180 or start_longitude < -180:
		return "start latitude out of bounds"
	if end_longitude > 180 or end_longitude < -180:
		return "start latitude out of bounds"

	if start_latitude < end_latitude:
		return "start latitude should be higher than end latitude"
	if start_longitude > end_longitude:
		return "start longitude should be lower than end longitude"

	res = []
	max_quakes = 0
	max_latitude = 0
	max_longitude = 0

	latitude = start_latitude
	lats = []
	while latitude > end_latitude:
		longitude = start_longitude
		longs = []
		while longitude < end_longitude:
			cur = connection.cursor()
			cur.execute("""select count(*) from all_month 
			where latitude between ? and ? and 
			longitude between ? and ?""", (latitude - step, latitude, longitude, longitude + step,))
			cnt = int(cur.fetchone()[0])
			st = ''
			st = st + str(latitude) + 'N ' + str(longitude) + 'W: '
			st = st + str(cnt)
			# longs.append(st)
			longs.append(cnt)
			longitude = longitude + step

			if cnt > max_quakes:
				max_quakes = cnt
				max_latitude = latitude
				max_longitude = longitude

		lats.append(longs)
		latitude = latitude - step
	res.append(lats)

	ret = {}
	ret["latitude"] = start_latitude
	ret["longitude"] = start_longitude
	ret["data"] = res[0]
	ret["max_quakes"] = max_quakes
	ret["max_latitude"] = max_latitude
	ret["max_longitude"] = max_longitude
	ret["step"] = step
	return render_template('prob4.html', result=ret)


# allow a user to give two location values (lat and long for two different locations)
# and show (list) the lat, long, and place (name), for every earthquake in that area (box)
@app.route('/query5', methods=["POST"])
def problem_5():
	start_latitude = float(request.form["start_latitude"])
	start_longitude = float(request.form["start_longitude"])

	end_latitude = float(request.form["end_latitude"])
	end_longitude = float(request.form["end_longitude"])


	if start_latitude > 90 or start_latitude < -90:
		return "start latitude out of bounds"
	if end_latitude > 90 or end_latitude < -90:
		return "end latitude out of bounds"
	if start_longitude > 180 or start_longitude < -180:
		return "start latitude out of bounds"
	if end_longitude > 180 or end_longitude < -180:
		return "start latitude out of bounds"

	if start_latitude < end_latitude:
		return "start latitude should be higher than end latitude"
	if start_longitude > end_longitude:
		return "start longitude should be lower than end longitude"

	cur = connection.cursor()
	cur.execute("""select latitude, longitude, place from all_month where latitude between ? and ? and 
	longitude between ? and ?""", (end_latitude, start_latitude, start_longitude, end_longitude,))
	result = cur.fetchall()
	return render_template('prob5.html', result=result)


# Delete based on input
@app.route('/query6', methods=["POST"])
def problem_6():
	start_magnitude = request.form["start_magnitude"]
	end_magnitude = request.form["end_magnitude"]

	if start_magnitude > end_magnitude:
		return "start magnitude greater than end magnitude"
	date = request.form["start_date"]
	cur = connection.cursor()
	cur.execute("""Select count(*) from all_month""", ())
	before_count = int(cur.fetchone()[0])
	cur.execute("""Delete from all_month 
	where date(REPLACE(REPLACE(TIME, 'Z', ' '), 'T', ' ')) = ? 
	and mag between ? and ?""", (date, start_magnitude, end_magnitude,))
	connection.commit()
	rdel = cur.rowcount
	after_count = before_count - rdel
	ret = "records deleted: " + str(rdel) + ", records remaining: " + str(after_count)

	return render_template('prob6.html', result=ret)



# Search for and count all earthquakes that occurred
# with a magnitude greater than 5.0
@app.route('/query1n', methods=["POST"])
def problem_1n():
	cc = request.form["ccode"]
	cur = conn.cursor()
	cur.execute("""SELECT latitude, longitude, name
	from latlong where country = ?""", (cc,))
	result = cur.fetchall()
	return render_template('prob1.html', result=result)


# show Country for pair of coordinates
@app.route('/query2n', methods=["POST"])
def problem_2n():
	start_latitude = float(request.form["start_latitude"])
	start_longitude = float(request.form["start_longitude"])

	end_latitude = float(request.form["end_latitude"])
	end_longitude = float(request.form["end_longitude"])


	if start_latitude > 90 or start_latitude < -90:
		return "start latitude out of bounds"
	if end_latitude > 90 or end_latitude < -90:
		return "end latitude out of bounds"
	if start_longitude > 180 or start_longitude < -180:
		return "start latitude out of bounds"
	if end_longitude > 180 or end_longitude < -180:
		return "start latitude out of bounds"

	cur = conn.cursor()
	cur.execute("""select name from latlong where latitude between ? and ? and 
	longitude between ? and ?""", (start_latitude, end_latitude, start_longitude, end_longitude,))
	result = cur.fetchall()
	return render_template('prob2.html', result=result)


# display the place, then the latitude,
# longitude, and time for all quakes within
@app.route('/query3', methods=["POST"])
def problem_3n():
	start_latitude = float(request.form["start_latitude"])
	start_longitude = float(request.form["start_longitude"])

	end_latitude = float(request.form["end_latitude"])
	end_longitude = float(request.form["end_longitude"])

	magnitude = float(request.form["magnitude"])


	if start_latitude > 90 or start_latitude < -90:
		return "start latitude out of bounds"
	if end_latitude > 90 or end_latitude < -90:
		return "end latitude out of bounds"
	if start_longitude > 180 or start_longitude < -180:
		return "start latitude out of bounds"
	if end_longitude > 180 or end_longitude < -180:
		return "start latitude out of bounds"

	cur = conn.cursor()
	cur.execute("""select place, latitude, longitude, time, mag from quakes where latitude between ? and ? and 
	longitude between ? and ? 
	and mag >= ?""", (start_latitude, end_latitude, start_longitude, end_longitude, magnitude,))
	result = cur.fetchall()
	return render_template('prob3.html', result=result)


# display the number
# of quakes in intervals of 1
@app.route('/querymagp', methods=["POST"])
def problem_mag_point_n():
	st_mag = float(request.form["start_nstm"])
	end_mag = float(request.form["end_nstm"])
	start_latitude = float(request.form["start_latitude"])
	start_longitude = float(request.form["start_longitude"])
	xc = float(request.form["end_latitude"])
	yc = float(request.form["end_longitude"])
	coefx = xc * 0.0089
	coefy = yc * 0.0089

	new_lat = start_latitude + coefx
	new_long = start_longitude + coefy / math.cos(xc * 0.018)
	cur = conn.cursor()
	ret = {}
	while st_mag < end_mag:
		cur.execute("""Select count(*) from (Select time, id, nst as nst, mag as mag from quakes
		where latitude between (?) and (?) and
		longitude between (?) and (?)) where
		mag between (?) and (?)""", (start_latitude, new_lat,
									 start_longitude, new_long,
									 st_mag, st_mag + 1,))
		result = cur.fetchone()
		ret["Magnitude " + str(st_mag) + " to " + str(st_mag + 1) + ", " +
			str(result[0]) + " earthquakes"] = result[0]
		st_mag = st_mag + 1

	return render_template('magpointinc.html', result=ret)


# display the place, then the latitude,
# longitude, and time for all quakes within
@app.route('/query3n', methods=["POST"])
def problem_3nn():
	start_latitude = float(request.form["start_latitude"])
	start_longitude = float(request.form["start_longitude"])

	xc = float(request.form["end_latitude"])
	yc = float(request.form["end_longitude"])

	magnitude = float(request.form["magnitude"])
	coefx = xc * 0.0089
	coefy = yc * 0.0089

	new_lat = start_latitude + coefx
	new_long = start_longitude + coefy / math.cos(xc * 0.018)
	print(new_lat)
	print(new_long)
	cur = conn.cursor()
	cur.execute("""select place, latitude, longitude, time, mag from quakes where latitude between ? and ? and 
	longitude between ? and ? 
	and mag >= ?""", (start_latitude, new_lat, start_longitude, new_long, magnitude,))
	result = cur.fetchall()
	return render_template('prob3n.html', result=result)


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=port)

