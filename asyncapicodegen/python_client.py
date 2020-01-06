import abc
import stringcase
import yaml

from . import templator
from . import specwrapper
from . import python_summary
import jsonschemacodegen.python
import jsonschemacodegen.resolver

class SimpleResolver(python_summary.SimpleResolver):
    pass

class GeneratorFromAsyncApi(python_summary.GeneratorFromAsyncApi):

    def Generate(self, spec, class_name, filename_base):
        assert(isinstance(spec, dict))
        wrappedSpec = specwrapper.SpecRoot(spec, self.resolver)

        self.GenerateSchemasForType(wrappedSpec, 'messages', lambda obj: obj['payload'])
        self.GenerateSchemasForType(wrappedSpec, 'schemas', lambda obj: obj)

        if 'channels' in wrappedSpec:
            clientType = 'x-client-role' in wrappedSpec and wrappedSpec['x-client-role'] or 'client'
            outputName = "{}.py".format(filename_base)
            self.generator.RenderTemplate("client.py.jinja2", 
                outputName, 
                Name = "{}{}".format(stringcase.pascalcase(class_name), stringcase.pascalcase(clientType)),
                spec = wrappedSpec,
                resolver=self.resolver)

