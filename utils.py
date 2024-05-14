import random


def sensor_data_generator():
    sensor_parameters = {
        "PM2.5": random.uniform(0, 100),  # µg/m³
        "PM10": random.uniform(0, 150),  # µg/m³
        "CO": random.uniform(0, 10),  # ppm
        "O3": random.uniform(0, 0.2),  # ppb
        "SO2": random.uniform(0, 1),  # ppb
        "NO2": random.uniform(0, 0.4)  # ppb
    }
    return sensor_parameters


def all_dict_vals_to_list(dict):
    return list(dict.values())
