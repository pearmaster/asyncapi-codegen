import abc
import stringcase

from . import templator
from . import specwrapper
import jsonschemacodegen.cpp

class GeneratedFiles(object):

    def __init__(self, cppFile=None, hppFile=None):
        self.cpp = []
        self.hpp = []
        if cppFile is not None:
            self.cpp.append(cppFile)
        if hppFile is not None:
            self.hpp.append(hppFile)

    def __iadd__(self, other):
        assert(isinstance(other, type(self)))
        self.cpp.extend(other.cpp)
        self.hpp.extend(other.hpp)
        return self

class ResolverBaseClass(abc.ABC):
    pass

class SimpleResolver(ResolverBaseClass, jsonschemacodegen.cpp.ResolverBaseClass):

    def GetReferenceParts(self, reference):
        pkg = None
        fn = reference.split('#')[0] or None
        path = reference.split('#')[1]
        parts = path.split('/')
        if fn:
            pkg = fn.split('.')[0]
        return (pkg, parts[-2], stringcase.pascalcase(parts[-1]))

    def GetHeader(self, reference):
        pkg, n, kls = self.GetReferenceParts(reference)
        return "%s%s%s_%s.hpp" % (pkg or '', pkg and '/' or '', n, stringcase.snakecase(kls))

    def GetNamespace(self, reference, usings=[], append=''):
        pkg, n, _kls = self.GetReferenceParts(reference)
        ns = []
        if pkg is not None:
            ns.append(stringcase.lowercase(pkg))
        ns.append(stringcase.lowercase(n))
        return self.ResolveNamespace(usings, ns, append)

    def GetName(self, reference):
        _pkg, _n, kls = self.GetReferenceParts(reference)
        return stringcase.pascalcase(kls)


class GeneratorFromAsyncApi(object):

    def __init__(self, src_output_dir, header_output_dir, resolver=None, namespace=[], src_usings=[]):
        self.output_dir = {
            "src": src_output_dir,
            "header": header_output_dir,
        }
        self.namespace = namespace
        self.usings = src_usings
        self.resolver = resolver

        self.srcGenerator = templator.Generator('asyncapicodegen.templates.cpp', self.output_dir['src'])
        self.headerGenerator = templator.Generator('asyncapicodegen.templates.cpp', self.output_dir['header'])

    def GenerateSchemasForType(self, spec, itemType, getSchemaFunc):
        assert(isinstance(spec, dict))
        genFiles = GeneratedFiles()
        pathBase = "#/components/%s/%s"
        if 'components' not in spec or itemType not in spec['components']:
            return genFiles
        for name, obj in spec['components'][itemType].items():
            ref = pathBase % (itemType, name)
            print("Generating for %s" % (ref))
            headerFileName = self.resolver.GetHeader(ref)
            fileBase = ".".join(headerFileName.split('.')[:-1])
            ns = self.resolver.GetNamespace(ref).split("::")
            schemaGenerator = jsonschemacodegen.cpp.GeneratorFromSchema(self.output_dir['src'], self.output_dir['header'],
                    self.resolver, ns, self.usings)
            output = schemaGenerator.Generate(getSchemaFunc(obj), stringcase.pascalcase(name), fileBase)
            assert(output is not None), "Generating {} didn't have output".format(name)
            genFiles += GeneratedFiles(*output)
        return genFiles

    def GenerateSchemas(self, spec):
        genFiles = GeneratedFiles()
        genFiles += self.GenerateSchemasForType(spec, 'parameters', lambda obj: obj['schema'])
        genFiles += self.GenerateSchemasForType(spec, 'messages', lambda obj: obj['payload'])
        genFiles += self.GenerateSchemasForType(spec, 'schemas', lambda obj: obj)
        return genFiles

    def GenerateServers(self, spec):
        genFiles = GeneratedFiles()
        for serverName, serverObj in spec['servers'].items():
            headerFilename = "server_%s.hpp" % (serverName.lower())
            sourceFilename = "server_%s.cpp" % (serverName.lower())
            self.srcGenerator.RenderTemplate("broker.cpp.jinja2", 
                sourceFilename, 
                usings=self.usings,
                ns=self.namespace, 
                resolver=self.resolver,
                includes=[headerFilename],
                Name=stringcase.pascalcase(serverName),
                server=serverObj)
            genFiles += GeneratedFiles(cppFile=sourceFilename)
            self.headerGenerator.RenderTemplate("broker.hpp.jinja2", 
                headerFilename,
                ns=self.namespace,
                resolver=self.resolver,
                Name=stringcase.pascalcase(serverName),
                server=serverObj)
            genFiles += GeneratedFiles(hppFile=headerFilename)
        return genFiles


    def Generate(self, spec, class_name, filename_base):
        assert(isinstance(spec, dict))
        wrappedSpec = specwrapper.SpecRoot(spec, self.resolver.loader)
        genFiles = GeneratedFiles()

        genFiles += self.GenerateSchemas(spec)
        genFiles += self.GenerateServers(wrappedSpec)

        args = {
            "Name": class_name,
            "spec": wrappedSpec,
        }
        headerFilename = "%s.hpp" % (filename_base)
        sourceFilename = "%s.cpp" % (filename_base)
        self.srcGenerator.RenderTemplate("source.cpp.jinja2", 
            sourceFilename, 
            usings=self.usings,
            ns=self.namespace, 
            resolver=self.resolver,
            includes=[headerFilename],
            **args)
        genFiles += GeneratedFiles(cppFile=sourceFilename)
        self.headerGenerator.RenderTemplate("header.hpp.jinja2", 
            headerFilename,
            ns=self.namespace,
            resolver=self.resolver,
            **args)
        genFiles += GeneratedFiles(hppFile=headerFilename)
        return genFiles
