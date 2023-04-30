import abc
import stringcase
import datetime

from jacobsjinjatoo import templator
from . import specwrapper
from . import _version
import jsonschemacodegen.cpp
import jsonschemacodegen.resolver

class GeneratedFiles(object):

    def __init__(self, cppFile=None, hppFile=None):
        self.cpp = []
        self.hpp = []
        if cppFile is not None:
            self.cpp.append(cppFile)
        if hppFile is not None:
            self.hpp.append(hppFile)

    def __iadd__(self, other):
        assert(isinstance(other, type(self)) or len(other) == 2)
        if isinstance(other, type(self)):
            self.cpp.extend(other.cpp)
            self.hpp.extend(other.hpp)
        elif len(other) == 2:
            if other[0] is not None:
                self.cpp.append(other[0])
            if other[1] is not None:
                self.hpp.append(other[1])
        else:
            raise "Runtime error"
        return self


class ResolverBaseClass(jsonschemacodegen.cpp.ResolverBaseClass):
    
    @abc.abstractmethod
    def cpp_get_client_filename_base(self, spec, uri):
        pass

    @abc.abstractmethod
    def cpp_get_client_classname(self, spec, uri):
        pass



class SimpleResolver(ResolverBaseClass, jsonschemacodegen.resolver.SimpleResolver):

    def cpp_get_client_filename_base(self, spec, uri):
        name = stringcase.snakecase(uri.split('.')[-1])
        return "asyncapi_{}_client".format(name)

    def cpp_get_client_classname(self, uri, spec):
        return stringcase.pascalcase(self.cpp_get_client_filename_base(uri, spec))


class GeneratorFromAsyncApi(object):

    def __init__(self, src_output_dir, header_output_dir, resolver, namespace=[], src_usings=[]):
        
        self.output_dir = {
            "src": src_output_dir,
            "header": header_output_dir,
        }
        self.namespace = namespace
        self.usings = src_usings
        self.resolver = resolver

        for u in src_usings:
            self.resolver.cpp_add_using(u)

        self.srcGenerator = templator.CodeTemplator(self.output_dir['src'])
        self.srcGenerator.add_template_package('asyncapicodegen.templates.cpp')
        self.srcGenerator.add_template_package('jsonschemacodegen.templates.cpp')
        self.headerGenerator = templator.CodeTemplator(self.output_dir['header'])
        self.headerGenerator.add_template_package('asyncapicodegen.templates.cpp')
        self.headerGenerator.add_template_package('jsonschemacodegen.templates.cpp')
        self.library_generator = jsonschemacodegen.cpp.LibraryGenerator(src_output_dir, header_output_dir, resolver)

    def GenerateSchemasForType(self, spec, url, itemType, getSchemaFunc):
        assert(isinstance(spec, specwrapper.SpecRoot))
        genFiles = GeneratedFiles()
        pathBase = "%s#/components/%s/%s"
        if 'components' not in spec or itemType not in spec['components']:
            return genFiles
        for name, obj in spec['components'][itemType].items():
            ref = pathBase % (url, itemType, name)
            schemaGenerator = jsonschemacodegen.cpp.GeneratorFromSchema(src_output_dir=self.output_dir['src'],
                    header_output_dir=self.output_dir['header'],
                    resolver=self.resolver)
            output = schemaGenerator.Generate(getSchemaFunc(obj), ref)
            assert(output is not None), "Generating {} didn't have output".format(name)
            genFiles += GeneratedFiles(*output)
        return genFiles

    def GenerateSchemas(self, spec, url):
        genFiles = GeneratedFiles()
        genFiles += self.GenerateSchemasForType(spec, url, 'parameters', lambda obj: obj['schema'])
        genFiles += self.GenerateSchemasForType(spec, url, 'messages', lambda obj: obj['payload'])
        genFiles += self.GenerateSchemasForType(spec, url, 'schemas', lambda obj: obj)
        return genFiles

    def GenerateServers(self, spec, url):
        genFiles = GeneratedFiles()
        if 'servers' in spec:
            for serverName, serverObj in spec['servers'].items():
                path = "{}#/servers/{}".format(url, serverName)
                headerFilename = self.resolver.cpp_get_header(path)
                sourceFilename = "{}.cpp".format(self.resolver.cpp_get_filename_base(path))
                name = stringcase.pascalcase(stringcase.snakecase(serverName))
                self.srcGenerator.render_template(template_name="broker.cpp.jinja2", 
                    output_name=sourceFilename, 
                    usings=self.resolver.cpp_get_usings(),
                    ns=self.namespace, 
                    resolver=self.resolver,
                    includes=[headerFilename],
                    Name=name,
                    server=serverObj)
                genFiles += GeneratedFiles(cppFile=sourceFilename)
                self.headerGenerator.render_template(template_name="broker.hpp.jinja2", 
                    output_name=headerFilename,
                    ns=self.namespace,
                    resolver=self.resolver,
                    Name=name,
                    server=serverObj)
                genFiles += GeneratedFiles(hppFile=headerFilename)
        return genFiles

    def Generate(self, spec, class_name):
        assert(isinstance(spec, dict))
        wrappedSpec = specwrapper.SpecRoot(spec, self.resolver)
        genFiles = GeneratedFiles()

        genFiles += self.GenerateSchemas(wrappedSpec, class_name)
        genFiles += self.GenerateServers(wrappedSpec, class_name)

        headerFilename = "{}.hpp".format(self.resolver.cpp_get_client_filename_base(wrappedSpec, class_name))
        sourceFilename = "{}.cpp".format(self.resolver.cpp_get_client_filename_base(wrappedSpec, class_name))
        self.srcGenerator.render_template(template_name="source.cpp.jinja2", 
            output_name=sourceFilename, 
            usings=self.usings,
            ns=self.namespace, 
            resolver=self.resolver,
            includes=[headerFilename],
            Name=class_name,
            codegenVersion=_version.__version__,
            codegenDate=datetime.datetime.now().strftime("%c"),
            spec=wrappedSpec)
        genFiles += GeneratedFiles(cppFile=sourceFilename)
        self.headerGenerator.render_template(template_name="header.hpp.jinja2", 
            output_name=headerFilename,
            ns=self.namespace,
            resolver=self.resolver,
            Name=class_name,
            codegenVersion=_version.__version__,
            codegenDate=datetime.datetime.now().strftime("%c"),
            spec=wrappedSpec)
        genFiles += GeneratedFiles(hppFile=headerFilename)
        genFiles += self.library_generator.Generate()
        return genFiles
