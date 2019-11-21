import stringcase
import os.path
import yaml

from . import templator
from . import specwrapper


class GeneratorFromAsyncApi(object):

    def __init__(self, output, resolver):
        self.output = output
        self.resolver = resolver
        self.generator = templator.Generator('asyncapicodegen.templates.markdown', os.path.dirname(self.output))

    def Generate(self, spec):
        assert(isinstance(spec, dict))
        wrappedSpec = specwrapper.SpecRoot(spec, self.resolver)

        outputName = "{}".format(os.path.basename(self.output))
        self.generator.RenderTemplate("summary.md.jinja2", 
            outputName,
            resolver=self.resolver,
            spec = wrappedSpec)
