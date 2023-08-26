from flask import Flask, request, render_template
import uuid
from xml.etree import ElementTree as ET
import pandas as pd
from cassandra.cluster import Cluster
import urllib.request

app = Flask(__name__)

# Function to build the API URL based on city ID or name
def url_builder(city_id, city_name, country):
    user_api = 'dd21a638583cc4d8d17e6e7b24b70348'
    unit = 'metric'

    if city_name != "":
        api = 'http://api.openweathermap.org/data/2.5/weather?q='
        full_api_url = api + str(city_name) + ',' + str(country) + '&mode=xml&units=' + unit + '&APPID=' + user_api
    else:
        api = 'http://api.openweathermap.org/data/2.5/weather?id='
        full_api_url = api + str(city_id) + '&mode=xml&units=' + unit + '&APPID=' + user_api

    return full_api_url

# Function to fetch data from the API and parse it in XML format
def data_fetch_XML(full_api_url):
    url = urllib.request.urlopen(full_api_url)
    xml_data = url.read().decode('utf-8')

    root = ET.fromstring(xml_data)  # Parse the XML data using ElementTree
    raw_api_dict = {}
    raw_api_dict['city_id'] = root.find('.//city').attrib['id']
    raw_api_dict['city_name'] = root.find('.//city').attrib['name']
    raw_api_dict['coord_lon'] = root.find('.//city/coord').attrib['lon']
    raw_api_dict['coord_lat'] = root.find('.//city/coord').attrib['lat']
    raw_api_dict['country'] = root.find('.//city/country').text
    raw_api_dict['timezone'] = root.find('.//city/timezone').text
    raw_api_dict['sun_rise'] = root.find('.//city/sun').attrib['rise']
    raw_api_dict['sun_set'] = root.find('.//city/sun').attrib['set']
    raw_api_dict['temperature_value'] = root.find('.//temperature').attrib['value']
    raw_api_dict['feels_like_value'] = root.find('.//feels_like').attrib['value']
    raw_api_dict['humidity_value'] = root.find('.//humidity').attrib['value']
    raw_api_dict['pressure_value'] = root.find('.//pressure').attrib['value']
    raw_api_dict['wind_speed_value'] = root.find('.//wind/speed').attrib['value']
    raw_api_dict['wind_direction_value'] = root.find('.//wind/direction').attrib['value']
    raw_api_dict['clouds_value'] = root.find('.//clouds').attrib['value']
    raw_api_dict['visibility_value'] = root.find('.//visibility').attrib['value']
    raw_api_dict['weather_value'] = root.find('.//weather').attrib['value']
    raw_api_dict['lastupdate_value'] = root.find('.//lastupdate').attrib['value']

    url.close()
    return raw_api_dict

def WriteXML(data):
    df = pd.DataFrame(data, index=[0])
    df.to_xml("weather_XML.xml", root_name='weathers', row_name='weather')
    return df

def setup_cassandra():
    cluster = Cluster(['127.0.0.1'])
    session = cluster.connect()

    session.execute("CREATE KEYSPACE IF NOT EXISTS weather_scraping WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 3};")
    session.execute("USE weather_scraping")

    session.execute("""
        CREATE TABLE IF NOT EXISTS weather_data (
            id uuid PRIMARY KEY,
            city_id text,
            city_name text,
            coord_lon text,
            coord_lat text,
            country text,
            timezone text,
            sun_rise text,
            sun_set text,
            temperature_value text,
            feels_like_value text,
            humidity_value text,
            pressure_value text,
            wind_speed_value text,
            wind_direction_value text,
            clouds_value text,
            visibility_value text,
            weather_value text,
            lastupdate_value text
        )
    """)

    return cluster, session

def close_cassandra(cluster, session):
    session.shutdown()
    cluster.shutdown()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        city_name = request.form.get('city_name')

        cluster, session = setup_cassandra()

        query = "SELECT * FROM weather_data WHERE city_name = %s ALLOW FILTERING"
        rows = session.execute(query, (city_name,))

        weather_data = []
        for row in rows:
            weather_data.append(row._asdict())

        if not weather_data:
            data_XML = data_fetch_XML(url_builder('', city_name, ''))
            dfJobs = WriteXML(data_XML)

            for row in dfJobs.itertuples(index=False):
                session.execute("""
                    INSERT INTO weather_data (
                        id, city_id, city_name, coord_lon, coord_lat, country, timezone, sun_rise, sun_set,
                        temperature_value, feels_like_value, humidity_value, pressure_value, wind_speed_value,
                        wind_direction_value, clouds_value, visibility_value, weather_value, lastupdate_value
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    uuid.uuid4(), row.city_id, row.city_name, row.coord_lon, row.coord_lat, row.country,
                    row.timezone, row.sun_rise, row.sun_set, row.temperature_value, row.feels_like_value,
                    row.humidity_value, row.pressure_value, row.wind_speed_value, row.wind_direction_value,
                    row.clouds_value, row.visibility_value, row.weather_value, row.lastupdate_value
                ))

            rows = session.execute(query, (city_name,))
            for row in rows:
                weather_data.append(row._asdict())

        close_cassandra(cluster, session)

        return render_template('index.html', weather_data=weather_data, city_name=city_name)
    else:
        return render_template('index.html', weather_data=None, city_name=None)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5008)

