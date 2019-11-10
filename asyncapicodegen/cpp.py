import abc
import stringcase

from . import templator
from . import specwrapper
import jsonschemacodegen.cpp

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
        cppFiles = []
        hppFiles = []
        pathBase = "#/components/%s/%s"
        if not itemType in spec['components']:
            return
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
            c, h = output
            if c is not None:
                cppFiles.append(c)
            if h is not None:
                hppFiles.append(h)
        return (cppFiles, hppFiles)

    def GenerateSchemas(self, spec):
        cppFiles = []
        hppFiles = []
        c, h = self.GenerateSchemasForType(spec, 'parameters', lambda obj: obj['schema'])
        cppFiles.extend(c)
        hppFiles.extend(h)
        c, h = self.GenerateSchemasForType(spec, 'messages', lambda obj: obj['payload'])
        cppFiles.extend(c)
        hppFiles.extend(h)
        c, h = self.GenerateSchemasForType(spec, 'schemas', lambda obj: obj)
        cppFiles.extend(c)
        hppFiles.extend(h)
        return (cppFiles, hppFiles)

    def GenerateServers(self, spec):
        hppFiles = []
        cppFiles = []
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
            cppFiles.append(sourceFilename)
            self.headerGenerator.RenderTemplate("broker.hpp.jinja2", 
                headerFilename,
                ns=self.namespace,
                resolver=self.resolver,
                Name=stringcase.pascalcase(serverName),
                server=serverObj)
            hppFiles.append(headerFilename)
        return (cppFiles, hppFiles)


    def Generate(self, spec, class_name, filename_base):
        assert(isinstance(spec, dict))
        wrappedSpec = specwrapper.SpecRoot(spec, self.resolver.loader)
        cppFiles = []
        hppFiles = []

        c, h = self.GenerateSchemas(spec)
        cppFiles.extend(c)
        hppFiles.extend(h)
        c, h = self.GenerateServers(wrappedSpec)
        cppFiles.extend(c)
        hppFiles.extend(h)

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
        cppFiles.append(sourceFilename)
        self.headerGenerator.RenderTemplate("header.hpp.jinja2", 
            headerFilename,
            ns=self.namespace,
            resolver=self.resolver,
            **args)
        hppFiles.append(headerFilename)
        return (cppFiles, hppFiles)
