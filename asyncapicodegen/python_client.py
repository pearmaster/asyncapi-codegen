import abc
import stringcase
import yaml

from jacobsjinjatoo import templator
from . import specwrapper
from . import python_summary
import jsonschemacodegen.python
import jsonschemacodegen.resolver


class SimpleResolver(python_summary.SimpleResolver):
    pass


class PackageResolver(SimpleResolver):

    def py_include_statement(self, reference):
        """Should return the include statement needed to acquire the object representing the
        schema pointed to at `reference`.  Example, "from schema_foo import Foo"
        """
        ref = self._get_reference_parts(reference)
        return "from . import {type}.{name}".format(**ref)

    def py_class_name(self, reference):
        """Should return the class name for the object representing the schema pointed to at `reference`.
        For example, "schema_foo.Foo"
        """
        ref = self._get_reference_parts(reference)
        return "{type}.{name}.{PascalName}".format(**ref)

    def py_filename(self, reference):
        """Should return the name of the filename holding the python class representing the schema pointed to
        at `reference`.  For example, "schema_foo.py"
        """
        ref = self._get_reference_parts(reference)
        return "{type}/{name}.py".format(**ref)

    def py_client_filepath(self, client_type, filename):
        return filename

    def py_package_name(self):
        return "asyncapi-client"

class GeneratorFromAsyncApi(python_summary.GeneratorFromAsyncApi):

    def Generate(self, spec, class_name, filename_base):
        assert(isinstance(spec, dict))
        wrappedSpec = specwrapper.SpecRoot(spec, self.resolver, class_name)

        self.GenerateSchemasForType(wrappedSpec, 'messages', lambda obj: obj['payload'])
        self.GenerateSchemasForType(wrappedSpec, 'schemas', lambda obj: obj)
        self.GenerateTestsForType(wrappedSpec, 'schemas', lambda obj: obj)
        self.GenerateTestsForType(wrappedSpec, 'messages', lambda obj: obj['payload'])

        if 'channels' in wrappedSpec:
            clientType = 'x-client-role' in wrappedSpec and wrappedSpec['x-client-role'] or 'client'
            outputName = self.resolver.py_client_filepath(clientType, "{}.py".format(filename_base))
            if outputName is not None:
                self.generator.render_template(template_name="client.py.jinja2", 
                    output_name=outputName, 
                    Name = "{}{}".format(stringcase.pascalcase(class_name), stringcase.pascalcase(clientType)),
                    spec = wrappedSpec,
                    resolver=self.resolver)
    
    def GenerateSetup(self, spec, class_name):
        assert(isinstance(spec, dict))
        wrappedSpec = specwrapper.SpecRoot(spec, self.resolver)
        clientType = 'x-client-role' in wrappedSpec and wrappedSpec['x-client-role'] or 'client'
        print(f"Generating setup for {clientType}")
        if clientType in ['provider', 'utilizer', 'library']:
            self.generator.render_template(template_name="setup.py.jinja2", 
                    output_name="setup.py", 
                    Name = "{}".format(stringcase.pascalcase(class_name)),
                    spec = wrappedSpec,
                    resolver=self.resolver)


