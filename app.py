from flask import Flask, render_template, jsonify
import models
import config
import utils

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('map.html')


@app.route('/get_sensor_locations')
def get_sensor_locations():
    # Retrieve all sensor geolocations from the database
    all_sensors_geo = models.get_all_sensor_geo()

    # Convert locations to dictionary format
    locations_data = [{'name': sensor.name, 'latitude': sensor.latitude, 'longitude': sensor.longitude}
                      for sensor in all_sensors_geo]

    return jsonify(locations_data)


if __name__ == '__main__':

    # if new environment and DB doesn't exist -> create basic 12 sensors and 6 parameters from config.py file
    for sensor_name in config.sensor_dict.keys():
        models.add_location(sensor_name, config.sensor_dict[sensor_name][0], config.sensor_dict[sensor_name][1])
    for parameter_name in config.parameters_dict.keys():
        models.add_parameter(parameter_name, config.parameters_dict[parameter_name])

    # get all sensor names
    sensor_names = models.get_all_sensor_names()

    # Receive measured concentrations data from sensor via MQTT protocol
    # (IRL: generating fake data but in practical ranges)
    parameter_values = {name: utils.sensor_data_generator() for name in sensor_names}

    # Loop through each sensor and operate its parameter concentration values
    for sensor_name, parameters in parameter_values.items():

        # get location_id of sensor
        location_id = models.session.query(models.Location.id).filter(models.Location.name == sensor_name).first()[0]

        # save concentrations data in measurement table
        for parameter_name, value in parameters.items():
            parameter_id = \
                models.session.query(models.Parameter.id).filter(models.Parameter.name == parameter_name).first()[0]
            models.add_measurement(location_id, parameter_id, value)

        # convert all concentration values with pollutant names as keys into -> list of consequent concentration values
        param_vals_list = utils.all_dict_vals_to_list(parameters)

        # calculating AQI: result = max AQI, all_pollutants_results = list of AQI values for each of pollutants
        result, all_pollutants_results = models.calculate_aqi(*param_vals_list)

        # add max AQI value as overall AQI at the moment
        models.add_aqi_result(location_id, result)

        # add each of pollutants AQI values in  aqi_pollutant_results
        [models.add_aqi_pollutant_result(location_id, sep_pollutant_name, sep_pollutant_result) for sep_pollutant_name,
        sep_pollutant_result in zip(config.pollutants_names_list, all_pollutants_results)]

    # Even if app just start up, we have updated database or at least basic data from config.py
    # Start Flask app for sensor data visualization
    app.run(debug=True)
