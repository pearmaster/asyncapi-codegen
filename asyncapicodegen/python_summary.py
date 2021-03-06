import abc
import stringcase
import yaml

from jacobsjinjatoo import templator
from . import specwrapper
import jsonschemacodegen.python
import jsonschemacodegen.resolver

class SimpleResolver(jsonschemacodegen.resolver.SimpleResolver):
    pass

class GeneratorFromAsyncApi(object):

    def __init__(self, output_dir, resolver=None):
        self.output_dir = output_dir
        self.resolver = resolver
        self.generator = templator.CodeTemplator(self.output_dir).add_template_package('asyncapicodegen.templates.python')

    def GenerateSchemasForType(self, spec, itemType, getSchemaFunc):
        files = []
        pathBase = "#/components/%s/%s"
        if 'components' not in spec or itemType not in spec['components']:
            return files
        for name, obj in spec['components'][itemType].items():
            ref = pathBase % (itemType, name)
            fileBase = self.resolver.py_filename(ref)
            if fileBase.endswith(".py"):
                fileBase = fileBase[:-3]
            schemaGenerator = jsonschemacodegen.python.GeneratorFromSchema(self.output_dir, self.resolver)
            output = schemaGenerator.Generate(getSchemaFunc(obj), spec, stringcase.pascalcase(name), fileBase)
            files.append(output)
        return files

    def GenerateTestsForType(self, spec, itemType, getSchemaFunc):
        files = []
        pathBase = "#/components/%s/%s"
        if 'components' not in spec or itemType not in spec['components']:
            return files
        for name, obj in spec['components'][itemType].items():
            ref = pathBase % (itemType, name)
            fileBase = self.resolver.py_filename(ref)
            if fileBase.endswith(".py"):
                fileBase = fileBase[:-3]
            schemaGenerator = jsonschemacodegen.python.GeneratorFromSchema(self.output_dir, self.resolver)
            schema = getSchemaFunc(obj)
            try:
                output = schemaGenerator.GenerateTestFromPath(schema, spec, ref)
            except:
                print(f"Failure generating test '{ref}' for scheam {schema} when root is {spec}")
                raise
            files.append(output)
        return files

    def Generate(self, spec, class_name, filename_base):
        assert(isinstance(spec, dict))
        wrappedSpec = specwrapper.SpecRoot(spec, self.resolver)

        self.GenerateSchemasForType(wrappedSpec, 'messages', lambda obj: obj['payload'])
        self.GenerateSchemasForType(wrappedSpec, 'schemas', lambda obj: obj)

        if 'channels' in wrappedSpec:
            outputName = self.resolver.py_client_filepath("summary", "{}.py".format(filename_base))
            self.generator.render_template(template_name="summary.py.jinja2", 
                output_name=outputName, 
                spec = wrappedSpec,
                resolver=self.resolver)

