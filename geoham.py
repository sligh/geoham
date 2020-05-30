from typing import Union
from geopy.distance import geodesic
from geopy.geocoders import Nominatim, options as geo_options
import certifi
import ssl
from math import radians, cos, sin, atan2, degrees
from maidenhead import toMaiden, toLoc

class Geoham():

    # A python class to handle various geo tasks (e.g., coordinates to address,
    #   address to coordinates, distance between two stations, bearing)

    # Justin Sligh, 2020

    def __init__(self):
        self.geo = None # Instantiates on first use.
        self.user_agent = 'Geoham/0.0.1' # This must be unique to your application

        # Python's certificates may become outdated. This fixes an error related to SSL.
        # TODO: Review. I assumed that setting scheme to http would bypass the problem but it dot not have an effect.
        self.ctx = ssl.create_default_context(cafile=certifi.where())
        geo_options.default_ssl_context = self.ctx

    def _format_and_combine_coordinates(self, a, b) -> list:
        a = self._format_coordinates(a)
        b = self._format_coordinates(b)

        pair = [a, b]

        return pair

    def _format_coordinates(self, coordinates) -> Union[list, None]:

        # Evaluate the input container
        if isinstance(coordinates, list):
            # TODO: Thought I might need to handle something specific.
            pass

        elif isinstance(coordinates, tuple):
            # get_bearing requires a list
            coordinates = [coordinates[0], coordinates[1]]

        elif isinstance(coordinates, dict) and isinstance(coordinates, dict):
            # Check for lat and lon then reformat for geopy
            if 'lat' in coordinates and 'lon' in coordinates:
                coordinates = [coordinates['lat'], coordinates['lon']]

            elif 'latitude' in coordinates and 'longitude' in coordinates:
                coordinates = [coordinates['latitude'], coordinates['longitude']]

            else:
                print('Error in Geoham get_distance. Coordinates not found in dictionary')
                return None

        elif isinstance(coordinates, str):
            # TODO: JS Handle Callsigns
            return None

        else:
            print('Error in Geoham _format_coordinates. Mixed types or unknown error.')
            return None

        # Convert to float
        try:
            coordinates[0] = float(coordinates[0])
            coordinates[1] = float(coordinates[1])
        except ValueError:
            print('Error in Geoham _format_coordinates. String does not contain number.')
            coordinates = None

        return coordinates

    def country_from_address(self, address) -> str:

        if isinstance(address, object):
            try:
                country = address['country']
            except:
                return ''

        return country

    def country_code_from_address(self, address) -> str:

        if isinstance(address, object):
            try:
                country_code = address['country_code']
            except:
                return ''

        return country_code

    def county_from_address(selfs, address) -> str:

        if isinstance(address, object):
            try:
                county = address['county']
            except:
                return ''

        return county

    def state_from_address(self, address) -> str:

        if isinstance(address, object):
            try:
                state = address['state']
            except:
                return ''

        return state

    def get_address_from_coodinates(self, coordinates) -> Union[object, None]:

        results = self.reverse_geocode(coordinates)

        return results

    def get_coordinates_from_address(self, address) -> Union[list, None]:

        results = self.geocode(address)

        try:
            coordinates = [float(results.raw['lat']), float(results.raw['lon'])]

        except:
            print('Error in Geoham get_coordinates_from_address. Address didnt return anything. Wow. That is rare.')
            return None

        return coordinates

    def get_bearing(self, a, b, rounded=True) -> Union[int, None]:

        station_coordinates = self._format_and_combine_coordinates(a, b)

        if station_coordinates:

            a = station_coordinates[0]
            b = station_coordinates[1]

            # A portion of jeromer's compassbearing from Github under public domain license
            try:
                lat1 = radians(a[0])
                lat2 = radians(b[0])
            except TypeError:
                print('Error in geoham get_bearing. Likely issue with coordiantes')
                return None

            diff_long = radians(b[1] - a[1])

            x = sin(diff_long) * cos(lat2)
            y = cos(lat1) * sin(lat2) - (sin(lat1) * cos(lat2) * cos(diff_long))

            initial_bearing = atan2(x, y)

            initial_bearing = degrees(initial_bearing)
            compass_bearing = (initial_bearing + 360) % 360

            if rounded:
                compass_bearing = round(compass_bearing)

            return compass_bearing

        else:

            return None

    def get_direction_from_coordinates(self, a, b) -> str:

        # Get the bearing
        bearing = self.get_bearing(a=a, b=b)

        direction = self.get_direction_from_bearing(bearing=bearing)

        return direction

    def get_direction_from_bearing(self, bearing) -> str:

        if not isinstance(bearing, int):
            print('Error in geoham get_direction_from_bearing. Invalid bearing')
            return None
        elif bearing > 360:
            print('Error in geoham get_direction_from_bearing. Invalid bearing. Over 360 degrees')
            return None

        # Convert to direction. Used some of Steve Gregory code in response to solution on stack.
        val = int((bearing / 22.5) + .5)

        arr = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]

        direction = arr[(val % 16)]

        return direction

    def get_distance(self, a, b, units='miles', rounded=True, label=False) -> Union[float, None]:

        station_coordinates = self._format_and_combine_coordinates(a, b)

        # Unpack Coordinates
        if station_coordinates:
            a = station_coordinates[0]
            b = station_coordinates[1]
        else:
            return None

        distance = geodesic(a, b)

        if distance != 0 and not None:

            # Convert to units
            if units == 'meters':
                distance = distance.meters
            elif units == 'kilometers':
                distance = distance.kilometers
            elif units == 'miles':
                distance = distance.miles
            elif units == 'feet':
                distance = distance.feet
            else:
                print('Error in Geoham get_distance. Unknown unit of measurement: ' + str(units))

            # Round

            if rounded:
                distance = round(distance)

        # Labels
        if label:
            distance = str(distance) + ' ' + units

        return distance

    def get_grid_from_coordinates(self, coordinates, precision=3) -> str:

        coordinates = self._format_coordinates(coordinates)

        if coordinates:
            grid = toMaiden(coordinates[0],coordinates[1],precision=precision)
            return grid
        else:
            return None

    def geocode(self, address) -> object:

        if not isinstance(address, str):
            print('Error in geoham get_coordinates. Expected a string but got something else')
            return None

        # Instantiate on first use
        if not self.geo:
            # TODO: Add ability to handle 403 and 429 errors caused by the useragent
            self.geo = Nominatim(scheme='https', user_agent=self.user_agent)

        results = self.geo.geocode(query=address, limit=1, language='en')

        return results

    def reverse_geocode(self, coordinates) -> object:

        '''
        :param coordinates:
        :return: object
            'place': 'College Park',
            'road': 'Venetian Avenue',
            'residential': 'University Heights',
            'hamlet': 'Fairvilla',
            'village': 'Fairview Shores',
            'county': 'Orange County',
            'state': 'Florida',
            'postcode': '32804',
            'country': 'United States of America',
            'country_code': 'us'
        '''

        # Instantiate on first use
        if not self.geo:
            # TODO: Add ability to handle 403 and 429 errors caused by the useragent
            self.geo = Nominatim(scheme='https', user_agent=self.user_agent)

        # Convert str coordinates to float
        lat = coordinates[0]
        lon = coordinates[1]
        if isinstance(lat, str) and isinstance(lon, str):
            try:
                lat = float(lat)
                lon = float(lon)
                coordinates = [lat, lon]
            except:
                pass

        try:
            result = self.geo.geocode(query=coordinates, limit=1, language='en', addressdetails=True)
            return result.raw['address']
        except:
            print('Error in Geoham reverse_geocode. Unknown results')

if __name__ == "__main__":
    geoham = Geoham()
