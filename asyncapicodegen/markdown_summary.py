import stringcase
import os.path
import yaml

from . import templator
from . import specwrapper

class Loader(object):
    
    def Load(self, uri):
        assert('yaml' in uri or 'yml' in uri), "Only YAML is supported at this time"
        with open(uri) as fp:
            spec = yaml.load(fp, Loader=yaml.FullLoader)
        return specwrapper.SpecRoot(spec, self)

class GeneratorFromAsyncApi(object):

    def __init__(self, output, loader=None):
        self.output = output
        self.loader = loader or Loader()
        self.generator = templator.Generator('asyncapicodegen.templates.markdown', os.path.dirname(self.output))

    def Generate(self, spec):
        assert(isinstance(spec, dict))
        wrappedSpec = specwrapper.SpecRoot(spec, self.loader)

        outputName = "{}".format(os.path.basename(self.output))
        self.generator.RenderTemplate("summary.md.jinja2", 
            outputName,
            loader=self.loader,
            spec = wrappedSpec)
