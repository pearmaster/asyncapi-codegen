import stringcase
import os.path
import yaml

from jacobsjinjatoo import templator
from . import specwrapper


class GeneratorFromAsyncApi(object):

    def __init__(self, output, resolver):
        self.output = output
        self.resolver = resolver
        self.generator = templator.MarkdownTemplator(os.path.dirname(self.output))
        self.generator.add_template_package('asyncapicodegen.templates.markdown')
        self.generator.add_template_package('jsonschemacodegen.templates.markdown')

    def Generate(self, spec):
        assert(isinstance(spec, dict))
        wrappedSpec = specwrapper.SpecRoot(spec, self.resolver)

        outputName = "{}".format(os.path.basename(self.output))
        self.generator.render_template(template_name="summary.md.jinja2", 
            output_name=outputName,
            resolver=self.resolver,
            spec = wrappedSpec)
