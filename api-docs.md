The OpenSky Network API documentation¶
This is the official documentation of the OpenSky Network’s live API. The API lets you retrieve live airspace information for research and non-commerical purposes.


OpenSky Python API¶
Our official Python implementation can be found on github in this repository. See the README for installation instructions.

Retrieving Data¶
The API is encapsulated in a single class with methods for data retrieving.

classopensky_api.OpenSkyApi(token_manager: TokenManager | None = None, client_id: str | None = None, client_secret: str | None = None)¶
Main class of the OpenSky Network API. Instances retrieve data from OpenSky via HTTP.

Authentication uses the OAuth2 client credentials flow. Pass either a TokenManager instance directly, or supply client_id / client_secret as keyword arguments. If neither is provided, requests are made anonymously (reduced rate limits apply).

The client holds an HTTP session and should be closed when no longer needed. The recommended pattern is to use it as a context manager:

with OpenSkyApi(token_manager=TokenManager.from_json_file("credentials.json")) as api:
    states = api.get_states()
__init__(token_manager: TokenManager | None = None, client_id: str | None = None, client_secret: str | None = None)¶
Create an instance of the API client.

Provide credentials in one of three ways (in order of precedence):

Pass a pre-built TokenManager via token_manager.

Pass client_id and client_secret directly.

Pass nothing → anonymous access (rate limits apply).

The credentials file produced by the OpenSky account page can be loaded conveniently with:

tm = TokenManager.from_json_file("credentials.json")
api = OpenSkyApi(token_manager=tm)
Parameters
:
token_manager (TokenManager) – a ready-to-use token manager (optional).

client_id (str) – OAuth2 client ID (optional).

client_secret (str) – OAuth2 client secret (optional).

get_arrivals_by_airport(airport, begin, end)¶
Retrieves flights for a certain airport which arrived within a given time interval [begin, end].

Begin and end must fall on the same UTC calendar day, or at most span a single day boundary (i.e. _count_utc_dates(begin, end) <= 1).

Parameters
:
airport (str) – ICAO identifier for the airport.

begin (int) – Start of time interval to retrieve flights for as Unix time (seconds since epoch).

end (int) – End of time interval to retrieve flights for as Unix time (seconds since epoch).

Returns
:
list of FlightData objects if request was successful, None otherwise.

Return type
:
list[FlightData] | None

get_departures_by_airport(airport, begin, end)¶
Retrieves flights for a certain airport which departed within a given time interval [begin, end].

Begin and end must fall on the same UTC calendar day, or at most span a single day boundary (i.e. _count_utc_dates(begin, end) <= 1).

Parameters
:
airport (str) – ICAO identifier for the airport.

begin (int) – Start of time interval to retrieve flights for as Unix time (seconds since epoch).

end (int) – End of time interval to retrieve flights for as Unix time (seconds since epoch).

Returns
:
list of FlightData objects if request was successful, None otherwise.

Return type
:
list[FlightData] | None

get_flights_by_aircraft(icao24, begin, end)¶
Retrieves data of flights for certain aircraft and time interval.

Parameters
:
icao24 (str) – Unique ICAO 24-bit address of the transponder in hex string representation. All letters need to be lower case.

begin (int) – Start of time interval to retrieve flights for as Unix time (seconds since epoch).

end (int) – End of time interval to retrieve flights for as Unix time (seconds since epoch).

Returns
:
list of FlightData objects if request was successful, None otherwise.

Return type
:
FlightData | None

get_flights_from_interval(begin, end)¶
Retrieves data of flights for certain time interval [begin, end].

Parameters
:
begin (int) – Start of time interval to retrieve flights for as Unix time (seconds since epoch).

end (int) – End of time interval to retrieve flights for as Unix time (seconds since epoch).

Returns
:
list of FlightData objects if request was successful, None otherwise.

Return type
:
FlightData | None

get_my_states(time_secs=0, icao24=None, serials=None)¶
Retrieve state vectors for your own sensors. Authentication is required for this operation. If time = 0 the most recent ones are taken. Optional filters may be applied for ICAO24 addresses and sensor serial numbers.

Parameters
:
time_secs (int) – time as Unix time stamp (seconds since epoch) or datetime. The datetime must be in UTC!

icao24 (str) – optionally retrieve only state vectors for the given ICAO24 address(es). The parameter can either be a single address as str or an array of str containing multiple addresses.

serials (int) – optionally retrieve only states of vehicles as seen by the given sensor(s). The parameter can either be a single sensor serial number (int) or a list of serial numbers.

Returns
:
OpenSkyStates if request was successful, None otherwise.

Return type
:
OpenSkyStates | None

get_states(time_secs=0, icao24=None, bbox=())¶
Retrieve state vectors for a given time. If time = 0 the most recent ones are taken. Optional filters may be applied for ICAO24 addresses.

Parameters
:
time_secs (int) – time as Unix time stamp (seconds since epoch) or datetime. The datetime must be in UTC!

icao24 (str) – optionally retrieve only state vectors for the given ICAO24 address(es). The parameter can either be a single address as str or an array of str containing multiple addresses.

bbox (tuple) – optionally retrieve state vectors within a bounding box. The bbox must be a tuple of exactly four values [min_latitude, max_latitude, min_longitude, max_longitude] each in WGS84 decimal degrees.

Returns
:
OpenSkyStates if request was successful, None otherwise.

Return type
:
OpenSkyStates | None

get_track_by_aircraft(icao24, t=0)¶
Retrieve the trajectory for a certain aircraft at a given time. The tracks endpoint is purely experimental.

Parameters
:
icao24 (str) – Unique ICAO 24-bit address of the transponder in hex string representation. All letters need to be lower case.

t (int) – Unix time in seconds since epoch. It can be any time between start and end of a known flight. If time = 0, get the live track if there is any flight ongoing for the given aircraft.

Returns
:
FlightTrack object if request was successful, None otherwise.

Return type
:
FlightTrack | None

Return Types¶
classopensky_api.OpenSkyStates(states_dict)¶
Represents the state of the airspace as seen by OpenSky at a particular time. It has the following fields:

time: int - in seconds since epoch (Unix time stamp). Gives the validity period of all states. All vectors represent the state of a vehicle with the interval [𝑡⁢𝑖⁢𝑚⁢𝑒 −1,𝑡⁢𝑖⁢𝑚⁢𝑒].
states: list [StateVector] - a list of StateVector or is None if there have been no states received.
classopensky_api.StateVector(arr)¶
Represents the state of a vehicle at a particular time. It has the following fields:

icao24: str - ICAO24 address of the transmitter in hex string representation.
callsign: str - callsign of the vehicle. Can be None if no callsign has been received.
origin_country: str - inferred through the ICAO24 address.
time_position: int - seconds since epoch of last position report. Can be None if there was no position report received by OpenSky within 15s before.
last_contact: int - seconds since epoch of last received message from this transponder.
longitude: float - in ellipsoidal coordinates (WGS-84) and degrees. Can be None.
latitude: float - in ellipsoidal coordinates (WGS-84) and degrees. Can be None.
geo_altitude: float - geometric altitude in meters. Can be None.
on_ground: bool - true if aircraft is on ground (sends ADS-B surface position reports).
velocity: float - over ground in m/s. Can be None if information not present.
true_track: float - in decimal degrees (0 is north). Can be None if information not present.
vertical_rate: float - in m/s, incline is positive, decline negative. Can be None if information not present.
sensors: list [int] - serial numbers of sensors which received messages from the vehicle within the validity period of this state vector. Can be None if no filtering for sensor has been requested.
baro_altitude: float - barometric altitude in meters. Can be None.
squawk: str - transponder code aka Squawk. Can be None.
spi: bool - special purpose indicator.
position_source: int - origin of this state’s position: 0 = ADS-B, 1 = ASTERIX, 2 = MLAT, 3 = FLARM
category: int - aircraft category: 0 = No information at all, 1 = No ADS-B Emitter Category Information, 2 = Light (< 15500 lbs), 3 = Small (15500 to 75000 lbs), 4 = Large (75000 to 300000 lbs), 5 = High Vortex Large (aircraft such as B-757), 6 = Heavy (> 300000 lbs), 7 = High Performance (> 5g acceleration and 400 kts), 8 = Rotorcraft, 9 = Glider / sailplane, 10 = Lighter-than-air, 11 = Parachutist / Skydiver, 12 = Ultralight / hang-glider / paraglider, 13 = Reserved, 14 = Unmanned Aerial Vehicle, 15 = Space / Trans-atmospheric vehicle, 16 = Surface Vehicle – Emergency Vehicle, 17 = Surface Vehicle – Service Vehicle, 18 = Point Obstacle (includes tethered balloons), 19 = Cluster Obstacle, 20 = Line Obstacle.
classopensky_api.FlightData(arr)¶
Class that represents data of certain flight. It has the following fields:

icao24: str - Unique ICAO 24-bit address of the transponder in hex string representation. All letters are lower case.
firstSeen: int - Estimated time of departure for the flight as Unix time (seconds since epoch).
estDepartureAirport: str - ICAO code of the estimated departure airport. Can be null if the airport could not be identified.
lastSeen: int - Estimated time of arrival for the flight as Unix time (seconds since epoch).
estArrivalAirport: str - ICAO code of the estimated arrival airport. Can be null if the airport could not be identified.
callsign: str - Callsign of the vehicle (8 chars). Can be null if no callsign has been received. If the vehicle transmits multiple callsigns during the flight, we take the one seen most frequently.
estDepartureAirportHorizDistance: int - Horizontal distance of the last received airborne position to the estimated departure airport in meters.
estDepartureAirportVertDistance: int - Vertical distance of the last received airborne position to the estimated departure airport in meters.
estArrivalAirportHorizDistance: int - Horizontal distance of the last received airborne position to the estimated arrival airport in meters.
estArrivalAirportVertDistance: int - Vertical distance of the last received airborne position to the estimated arrival airport in meters.
departureAirportCandidatesCount: int - Number of other possible departure airports. These are airports in short distance to estDepartureAirport.
arrivalAirportCandidatesCount: int - Number of other possible arrival airports. These are airports in short distance to estArrivalAirport.
classopensky_api.Waypoint(arr)¶
Class that represents the single waypoint that is a basic part of flight trajectory:

time: int - Time which the given waypoint is associated with in seconds since epoch (Unix time).
latitude: float - WGS-84 latitude in decimal degrees. Can be null.
longitude: float - WGS-84 longitude in decimal degrees. Can be null.
baro_altitude: float - Barometric altitude in meters. Can be null.
true_track: float - True track in decimal degrees clockwise from north (north=0°). Can be null.
on_ground: bool - Boolean value which indicates if the position was retrieved from a surface position report.
classopensky_api.FlightTrack(arr)¶
Class that represents the trajectory for a certain aircraft at a given time.:

icao24: str - Unique ICAO 24-bit address of the transponder in lower case hex string representation.
startTime: int - Time of the first waypoint in seconds since epoch (Unix time).
endTime: int - Time of the last waypoint in seconds since epoch (Unix time).
calllsign: str - Callsign (8 characters) that holds for the whole track. Can be null.
path: list [Waypoint] - waypoints of the trajectory.
Examples¶
Without any authentication you should only retrieve state vectors every 10 seconds. Any higher rate is unnecessary due to the rate limitations and strongly advised against. Example for retrieving all states without authentication:

from opensky_api import OpenSkyApi

api = OpenSkyApi()
states = api.get_states()
for s in states.states:
    print("(%r, %r, %r, %r)" % (s.longitude, s.latitude, s.baro_altitude, s.velocity))
Example for retrieving all state vectors currently received by your receivers (no rate limit):

from opensky_api import OpenSkyApi

api = OpenSkyApi(USERNAME, PASSWORD)
states = api.get_my_states()
print(states)
for s in states.states:
    print(s.sensors)
It is also possible to retrieve state vectors for a certain area. For this purpose, you need to provide a bounding box. It is defined by lower and upper bounds for longitude and latitude. The following example shows how to retrieve data for a bounding box which encompasses Switzerland:

from opensky_api import OpenSkyApi

api = OpenSkyApi()
# bbox = (min latitude, max latitude, min longitude, max longitude)
states = api.get_states(bbox=(45.8389, 47.8229, 5.9962, 10.5226))
for s in states.states:
    print("(%r, %r, %r, %r)" % (s.longitude, s.latitude, s.baro_altitude, s.velocity))
You can retrieve FlightData from a specific time interval, using the get_flights_from_interval method. To do this, provide the beginning and end of the time period, as a timestamps. It’s important, that provided time interval must not be greater than 2 hours. The following example shows how to retrieve the FlightData frames from 12pm to 1pm on Jan 29 2018:

from opensky_api import OpenSkyApi
api = OpenSkyApi()
data = api.get_flights_from_interval(1517227200, 1517230800)
for flight in data:
    print(flight)
The get_flights_by_aircraft method enables you to retrieve flights of a certain aircraft in time interval. To do this, specify the unique ICAO 24-bit aircraft address in hex string representation, the beginning and end of the time interval in the form of timestamps. The time interval must be smaller than 30 days. The example below shows steps to follow to get flights for D-AIZZ (3c675a), on Jan 29 2018:

from opensky_api import OpenSkyApi
api = OpenSkyApi()
data = api.get_flights_by_aircraft("3c675a", 1517184000, 1517270400)
for flight in data:
    print(flight)
It’s possible to retrieve arrivals and departures for a specific airport and time interval, using get_arrivals_by_airport and get_departures_by_airport methods. Both methods require the ICAO identifier for the airport, start and end of the time period. The time interval must be smaller than 7 days. The following code shows how to retrieve the arrivals and departures at Frankfurt International Airport (EDDF) from 12pm to 1pm on Jan 29 2018:

from opensky_api import OpenSkyApi
api = OpenSkyApi()
arrivals = api.get_arrivals_by_airport("EDDF", 1517227200, 1517230800)
departures = api.get_departures_by_airport("EDDF", 1517227200, 1517230800)
print("Arrivals:")
for flight in arrivals:
    print(flight)
print("Departures:")
for flight in departures:
    print(flight)
The get_track_by_aircraft method enables you to retrieve trajectory of the aircraft. Trajectory is given as a list of waypoints containing position, barometric altitude, true track and on-ground flag. In order to get the trajectory of the certain aircraft, you need to provide unique ICAO 24-bit aircraft address in hex string representation and optionally the timestamp between the start and end of a flight to be tracked. The default value of the timestamp, for the live tracking is 0. It is not possible to access flight tracks from more than 30 days in the past. The example below shows how to get the live track for aircraft with transponder address 3c4b26 (D-ABYF):

from opensky_api import OpenSkyApi
api = OpenSkyApi()
track = api.get_track_by_aircraft("3c4b26")
print(track)