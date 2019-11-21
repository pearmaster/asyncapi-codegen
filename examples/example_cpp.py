import asyncapicodegen.cpp
import sys
import yaml
import stringcase
from pprint import pprint
import urllib.request

if __name__ == '__main__':

    with urllib.request.urlopen("https://raw.githubusercontent.com/asyncapi/asyncapi/master/examples/2.0.0/streetlights.yml") as fp:
        spec = yaml.load(fp, Loader=yaml.FullLoader)

    # Dumb yaml importer interprets "on"/"off" as True/False
    spec['components']['schemas']['turnOnOffPayload']['properties']['command']['enum'] = ["on", "off"]

    name = 'streetlights'

    resolver = asyncapicodegen.cpp.SimpleResolver(name)
    generator = asyncapicodegen.cpp.GeneratorFromAsyncApi('output', 'output', resolver, ['ex'], [['ex']])
    generator.Generate(spec, name)
