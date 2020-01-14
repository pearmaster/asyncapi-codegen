import collections
import stringcase
import re
from jsonschemacodegen import json_example
import json

class BaseDict(collections.UserDict):

    def __init__(self, root, initialdata):
        assert(isinstance(root, SpecRoot))
        super().__init__(initialdata)
        self.root = root


class Parameter(BaseDict):

    def __init__(self, root, initialdata, name):
        super().__init__(root, initialdata)
        self.name = name
        if 'schema' in self.data and 'description' not in self.data['schema'] and 'description' in self.data:
            self.data['schema']['description'] = self.data['description']

    def GetType(self, resolver):
        if '$ref' in self.data:
            return resolver.cpp_get_ns_name(self.data['$ref'])
        elif 'schema' in self.data and 'type' in self.data['schema']:
            if self.data['schema']['type'] == 'integer':
                return 'int'
            elif self.data['schema']['type'] == 'string' and 'enum' not in self.data:
                return resolver.cpp_resolve_namespace(['std'])+'string'
            elif self.data['schema']['type'] == 'boolean':
                return 'bool'
        raise NotImplementedError

    def GetEnglishType(self, resolver):
        thedata = self.data
        if '$ref' in self.data:
            param = self.root.Resolve(self.data['$ref'], Parameter, name=self.name)
            engType = param.GetEnglishType(resolver)
            return engType
        assert('schema' in thedata)

        def GetEnglishTypeForSchema(root, resolver, sch):
            schema = sch
            if '$ref' in schema:
                schema = root.Resolve(schema['$ref'])
            if 'enum' in schema:
                return " OR ".join([f'"{e}"' for e in schema['enum']])
            if 'type' in schema:
                return schema['type']
            if 'oneOf' in schema:
                try:
                    alternatives = set([GetEnglishTypeForSchema(root, resolver, s) for s in schema['oneOf']])
                except:
                    return ""
                return " OR ".join([ f"[{a}]" for a in alternatives])
            return schema
        
        engType = GetEnglishTypeForSchema(self.root, resolver, thedata['schema'])
        return engType

    def __hash__(self):
        if '$ref' in self.data:
            return hash(self.data['$ref'])
        else:
            return 1

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()


class Operation(BaseDict):
    
    def __init__(self, root, operationType, initialdata):
        super().__init__(root, initialdata)
        self.operationType = operationType
        if 'traits' in self.data:
            for trait in self.data['traits']:
                if '$ref' in trait:
                    trait = self.root.Resolve(trait['$ref'], Trait)
                for k, v in trait.items():
                    assert(k not in ['message', 'traits'])
                    self.data[k] = v
        if 'bindings' in self.data and '$ref' in self.data['bindings']:
            self.data['bindings'] = self.root.Resolve(self.data['bindings']['$ref'], Binding)

    def Message(self):
        if 'message' in self.data:
            if '$ref' in self.data['message']:
                return self.root.Resolve(self.data['message']['$ref'], asClass=Message)
            else:
                return Message(self.root, self.data['message'])

    def GetMessageType(self, resolver):
        """ TODO: Rename this to Cpp
        """
        if 'message' in self.data and '$ref' in self.data['message']:
            return resolver.cpp_get_ns_name(self.data['message']['$ref'])
        else:
            print (self.data)
            raise NotImplementedError

    def Examples(self, resolver):
        generator = json_example.GeneratorFromSchema(resolver)
        if '$ref' in self.data['message']:
            try:
                doc = resolver.get_document(self.data['message']['$ref'])
            except KeyError:
                doc = self.root
            message_json = resolver.get_json(self.data['message']['$ref'], doc)
            try:
                examples = generator.Generate(doc, message_json['payload'])
            except KeyError as e:
                print(f"Couldn't find 'payload' in {message_json}")
                raise e
        else:
            examples = generator.Generate(self.root, self.data['message']['payload'])
        exampleList = [json.dumps(ex, indent=2, sort_keys=True) for ex in examples]
        sorted(exampleList, reverse=True)
        return exampleList

    def GetQoS(self, default=None):
        try:
            return int(self.data['bindings']['mqtt']['qos'])
        except:
            return default

    def GetRetain(self, default=None):
        try:
            return bool(self.data['bindings']['mqtt']['retain'])
        except:
            return default

    def HasTag(self, tagName):
        if 'tags' in self.data:
            for tag in self.data['tags']:
                if tag['name'] == tagName:
                    return True
        return False

    def GetTagNote(self, tagName):
        if 'tags' in self.data:
            for tag in self.data['tags']:
                if tag['name'] == tagName:
                    if 'x-note' in tag:
                        return tag['x-note']
                    if 'description' in tag:
                        return tag['description']
        return ''

    def CppAdditionalMqttParams(self, including=['qos', 'retain']):
        ret = []
        if 'qos' in including and self.GetQoS() is None:
            ret.append("int qos")
        if 'retain' in including and self.GetRetain() is None:
            ret.append("bool retain")
        return "%s%s" % (len(ret) > 0 and ', ' or '', ", ".join(ret))


class ChannelItem(BaseDict):

    def __init__(self, root, channelPath, initialdata):
        if 'publish' in initialdata:
            initialdata['publish'] = Operation(root, 'publish', initialdata['publish'])
        if 'subscribe' in initialdata:
            initialdata['subscribe'] = Operation(root, 'subscribe', initialdata['subscribe'])
        if 'parameters' in initialdata:
            for pName, pObj in initialdata['parameters'].items():
                initialdata['parameters'][pName] = Parameter(root, pObj, pName)

        super().__init__(root, initialdata)
        self.channelPath = channelPath

    def CppParamList(self, resolver, names=True, types=True, constRef=True, prepend='', append=''):
        params = []
        try:
            prepend = len(self.data['parameters']) > 0 and prepend or ''
            append = len(self.data['parameters']) > 0 and append or ''
            for paramName, paramObj in self.data['parameters'].items():
                params.append((stringcase.camelcase(paramName), paramObj.GetType(resolver)))
        except KeyError:
            append = ''
            prepend = ''
        s = prepend
        i = 0
        for name, theType in params:
            if i != 0:
                s += ", "
            i += 1
            if types:
                if constRef:
                    s += "const %s&" % (theType)
                else:
                    s += theType
                if names:
                    s += ' '
            if names:
                s += name
        s += append
        return s

    def GetName(self):
        return 'subscribe' in self.data and self.data['subscribe']['operationId'] or self.data['publish']['operationId']

    def GetPathAsBoostFormat(self):
        if '%' in self.channelPath:
            raise NotImplementedError
        pattern = r"\{\w+\}"
        def repl(_):
            repl.i += 1
            return f"%{repl.i}%"
        repl.i = 0
        return re.sub(pattern, repl, self.channelPath)

    def GetPathParameters(self):
        pattern = r"\{\w+\}"
        results = re.findall(pattern, self.channelPath)
        assert(len(results) == len(self.Parameters())), f"Mismatch of parameters from {self.GetName()}"
        return results

    def GetSubscribePath(self):
        pattern = r"\{\w+\}"
        return re.sub(pattern, '+', self.channelPath)

    def GetPathParts(self):
        return self.channelPath.split("/")

    def Parameters(self):
        if 'parameters' in self.data:
            return [(k,v) for k,v in self.data['parameters'].items()]
        return {}


class Channels(BaseDict):

    def __init__(self, root, initialdata):
        newDict = {}
        for k, v in initialdata.items():
            newDict[k] = ChannelItem(root, k, v)
        super().__init__(root, newDict)

    def GetAllParameters(self):
        params = set()
        for channel in self.data.values():
            if 'parameters' in channel:
                for param in channel['parameters'].items():
                    params.add(param)
        return params

    def CppGetDependencies(self, resolver):
        deps = set()
        params = self.GetAllParameters()
        for p in params:
            if '$ref' in p[1]:
                deps.add('"{}"'.format(resolver.cpp_get_header(p[1]['$ref'])))
        for chItem in self.data.values():
            for op in ['subscribe', 'publish']:
                if op in chItem:
                    if '$ref' in chItem[op]['message']:
                        deps.add('"%s"' % (resolver.cpp_get_header(chItem[op]['message']['$ref'])))
        return deps

    def PyGetIncludes(self, resolver):
        deps = set()
        for chItem in self.data.values():
            for op in ['subscribe', 'publish']:
                if op in chItem:
                    if '$ref' in chItem[op]['message']:
                        deps.add(resolver.py_include_statement(chItem[op]['message']['$ref']))
        return deps

class ServerObject(BaseDict):

    def __init__(self, root, name, initialdata):
        super().__init__(root, initialdata)
        self.name = name

        if self.data['protocol'] != 'mqtt':
            raise NotImplementedError(f"{self.data} is not a supported protocol")
        if 'protocolVersion' in self.data and self.data['protocolVersion'] != "3.1":
            raise NotImplementedError

    def GetUrl(self, partIndex=None):
        pattern = r"\{\w+\}"
        def repl(_):
            repl.i += 1
            return "%%%d%%" % (repl.i)
        repl.i = 0
        urlPart = self.data['url']
        if partIndex is not None:
            urlPart = self.data['url'].split(':')[partIndex]
        return {
            "raw": urlPart,
            "boostFormat": re.sub(pattern, repl, urlPart),
            "parameters": [x.strip('{}') for x in re.findall(pattern, urlPart)],
        }

    def GetHost(self):
        return self.GetUrl(0)

    def GetPort(self):
        return self.GetUrl(1)

    def TryGetBinding(self, name):
        try:
            return self.data['bindings'][self.data['protocol']][name]
        except:
            return None

    def IDontKnowWhatThisDeadCodeIs(self):
        if 'security' in self.data:
            for schemeName in self.data['security'].keys():
                scheme = self.root['components']['securitySchemes'][schemeName]
                if scheme['type'] != 'userPassword':
                    raise NotImplementedError

    def AcceptsUsernamePassword(self):
        if 'security' in self.data:
            for securityDef in self.data['security']:
                for schemeName, schemeDetails in securityDef.items():
                    scheme = self.root['components']['securitySchemes'][schemeName]
                    if scheme['type'] == 'userPassword':
                        return True
        return False


class Binding(BaseDict):
    def __init__(self, root, initialdata, name=None):
        super().__init__(root, initialdata)
        self.name = name
        if '$ref' in self.data:
            self.data = self.root.Resolve(self.data['$ref'], Binding)

    def __repr__(self):
        return f"Binding<{self.name}>"

class Trait(BaseDict):

    def __init__(self, root, initialdata, name=None):
        super().__init__(root, initialdata)
        self.name = name

        if 'bindings' in initialdata and '$ref' in initialdata['bindings']:
            self.data['bindings'] = self.root.Resolve(initialdata['bindings']['$ref'], Binding, name=initialdata['bindings']['$ref'])

    def __repr__(self):
        return f"Trait<{self.name}>"

class Servers(BaseDict):

    def __init__(self, root, initialdata):
        newDict = {}
        for k, v in initialdata.items():
            try:
                newDict[k] = ServerObject(root, k, v)
            except NotImplementedError:
                # Skip servers that are unsupported
                pass
        super().__init__(root, newDict)


class Message(BaseDict):

    def __init__(self, root, initialdata):
        super().__init__(root, initialdata)

    def Schema(self):
        assert('payload' in self.data['payload'])
        if '$ref' in self.data['payload']:
            return self.root.Resolve(self.data['payload']['$ref'])
        return self.data['payload']


class Components(BaseDict):

    def __init__(self, root, initialdata):
        super().__init__(root, initialdata)
        if 'messages' in self.data:
            for msgKey, msg in self.data['messages'].items():
                self.data['messages'][msgKey] = Message(root, msg)

class SpecRoot(BaseDict):
    
    def __init__(self, initialdata, resolver=None, name=None):
        super().__init__(self, initialdata)
        self.resolver = resolver
        self.name = name

        if self.data['asyncapi'] != '2.0.0':
            raise NotImplementedError

        if 'channels' in self.data:
            self.data['channels'] = Channels(self, self.data['channels'])

        if 'components' in self.data:
            self.data['components'] = Components(self, self.data['components'])

        if 'servers' in self.data:
            self.data['servers'] = Servers(self, self.data['servers'])

    def Resolve(self, ref, asClass=None, **kwargs):
        if len(ref.split('#')[0]) == 0:
            otherRoot = self
        else:
            otherRoot = SpecRoot(self.resolver.get_document(ref), self.resolver, name=ref.split('#')[0])
        if asClass is not None:
            theJson = otherRoot.resolver.get_json(ref, root=otherRoot)
            inst = asClass(otherRoot, theJson, **kwargs)
            return inst
        else:
            return self.resolver.get_schema(ref, root=otherRoot)

    def __repr__(self):
        return f"Spec<{self.name}>"
