
from typing import Any

import jsonschemacodegen
from jacobsjinjatoo import templator

from . import specwrapper

class Generator(object):

    def __init__(self, output_dir: str):
        self._output_dir = output_dir
        self._resolver = jsonschemacodegen.resolver.SimpleResolver("")
        self._generator = templator.CodeTemplator(self._output_dir)
        self._generator.add_template_package('asyncapicodegen.templates.c')
    
    
    def generate(self, spec: dict[str, Any]):
        assert(isinstance(spec, dict))
        wrapped_spec = specwrapper.SpecRoot(spec, self._resolver)

        for output_name in [
            'topics.h',
            'topics.c',
            'mqtt_client.c',
            'mqtt_client.h',
        ]:

            template_name = f"{output_name}.jinja2"

            self._generator.render_template(
                template_name=template_name, 
                output_name=output_name,
                spec=wrapped_spec
            )