import asyncapicodegen.python_client as pygen
import os
import yaml
import stringcase

if __name__ == '__main__':

    this_directory = os.path.dirname(os.path.abspath(__file__))
    output_directory = os.path.join(this_directory, "output_py")
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    with open(os.path.join(this_directory, "streetlights-mqtt.yml")) as fp:
        spec = yaml.load(fp, Loader=yaml.FullLoader)

    # Dumb yaml importer interprets "on"/"off" as True/False
    spec['components']['schemas']['turnOnOffPayload']['properties']['command']['enum'] = ["on", "off"]

    name = 'streetlights'

    resolver = pygen.SimpleResolver(name)
    pyGenerator = pygen.GeneratorFromAsyncApi(output_directory, resolver)
    pyGenerator.Generate(spec, stringcase.pascalcase(name), name)
