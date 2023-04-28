import asyncapicodegen.cpp
import os
import yaml


if __name__ == '__main__':

    this_directory = os.path.dirname(os.path.abspath(__file__))
    output_directory = os.path.join(this_directory, "output_cpp")
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    with open(os.path.join(this_directory, "streetlights-mqtt.yml")) as fp:
        spec = yaml.load(fp, Loader=yaml.FullLoader)

    # Dumb yaml importer interprets "on"/"off" as True/False
    spec['components']['schemas']['turnOnOffPayload']['properties']['command']['enum'] = ["on", "off"]

    name = 'Streetlights'

    resolver = asyncapicodegen.cpp.SimpleResolver(name)
    generator = asyncapicodegen.cpp.GeneratorFromAsyncApi(output_directory, output_directory, resolver, ['ex'], [['ex']])
    generator.Generate(spec, name)
