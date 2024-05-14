import models
import config
import utils

# if new environment and DB doesn't exist -> create basic 12 sensors and 6 parameters from config.py file
for sensor_name in config.sensor_dict.keys():
    aqm_db.add_location(sensor_name, config.sensor_dict[sensor_name][0], config.sensor_dict[sensor_name][1])
for parameter_name in config.parameters_dict.keys():
    aqm_db.add_parameter(parameter_name, config.parameters_dict[parameter_name])

# get all sensor names
sensor_names = aqm_db.get_all_sensor_names()

# Receive measured concentrations data from sensor via MQTT protocol
# (IRL: generating fake data but in practical ranges)
parameter_values = {name: utils.sensor_data_generator() for name in sensor_names}

# Loop through each sensor and operate its parameter concentration values
for sensor_name, parameters in parameter_values.items():

    # get location_id of sensor
    location_id = aqm_db.session.query(aqm_db.Location.id).filter(aqm_db.Location.name == sensor_name).first()[0]

    # save concentrations data in measurement table
    for parameter_name, value in parameters.items():
        parameter_id = \
            aqm_db.session.query(aqm_db.Parameter.id).filter(aqm_db.Parameter.name == parameter_name).first()[0]
        aqm_db.add_measurement(location_id, parameter_id, value)

    # convert all concentration values with pollutant names as keys into -> list of consequent concentration values
    param_vals_list = utils.all_dict_vals_to_list(parameters)

    # calculating AQI: result = max AQI, all_pollutants_results = list of AQI values for each of pollutants
    result, all_pollutants_results = aqm_db.calculate_aqi(*param_vals_list)

    # add max AQI value as overall AQI at the moment
    aqm_db.add_aqi_result(location_id, result)

    # add each of pollutants AQI values in  aqi_pollutant_results
    [aqm_db.add_aqi_pollutant_result(location_id, sep_pollutant_name, sep_pollutant_result) for sep_pollutant_name,
    sep_pollutant_result in zip(config.pollutants_names_list, all_pollutants_results)]
