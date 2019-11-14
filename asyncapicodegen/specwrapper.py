import collections
import stringcase
import re

class BaseDict(collections.UserDict):

    def __init__(self, root, initialdata):
        super().__init__(initialdata)
        self.root = root


class Parameter(BaseDict):

    def __init__(self, root, name, initialdata):
        super().__init__(root, initialdata)
        self.name = name
        if 'schema' in self.data and 'description' not in self.data['schema'] and 'description' in self.data:
            self.data['schema']['description'] = self.data['description']

    def GetType(self, resolver, namespace, usings):
        if '$ref' in self.data:
            return resolver.GetNamespace(self.data['$ref'], usings, '::')+resolver.GetName(self.data['$ref'])
        elif 'schema' in self.data and 'type' in self.data['schema']:
            if self.data['schema']['type'] == 'integer':
                return 'int'
            elif self.data['schema']['type'] == 'string' and 'enum' not in self.data:
                return resolver.ResolveNamespace(usings, ['std'], '::')+'string'
            elif self.data['schema']['type'] == 'boolean':
                return 'bool'
        raise NotImplementedError

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
                    if k not in ['message', 'traits']:
                        self.data[k] = v
        if 'bindings' in self.data and '$ref' in self.data['bindings']:
            self.data['bindings'] = self.root.Resolve(self.data['bindings']['$ref'])

    def GetMessageType(self, resolver, namespace, usings):
        if 'message' in self.data and '$ref' in self.data['message']:
            return resolver.GetNamespace(self.data['message']['$ref'], usings, '::')+resolver.GetName(self.data['message']['$ref'])
        else:
            print (self.data)
            raise NotImplementedError

    def GetQoS(self):
        try:
            return int(self.data['bindings']['mqtt']['qos'])
        except:
            return None

    def GetRetain(self):
        try:
            return bool(self.data['bindings']['mqtt']['retain'])
        except:
            return None

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
            initialdata['subscribe'] = Operation(root, 'publish', initialdata['subscribe'])
        if 'parameters' in initialdata:
            for pName, pObj in initialdata['parameters'].items():
                initialdata['parameters'][pName] = Parameter(root, pName, pObj)

        super().__init__(root, initialdata)
        self.channelPath = channelPath

    def CppParamList(self, resolver, namespace, usings, names=True, types=True, constRef=True, prepend='', append=''):
        params = []
        try:
            prepend = len(self.data['parameters']) > 0 and prepend or ''
            append = len(self.data['parameters']) > 0 and append or ''
            for paramName, paramObj in self.data['parameters'].items():
                params.append((stringcase.camelcase(paramName), paramObj.GetType(resolver, namespace, usings)))
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
            return "%{}%".format(repl.i)
        repl.i = 0
        return re.sub(pattern, repl, self.channelPath)

    def GetPathParameters(self):
        pattern = r"\{\w+\}"
        return re.findall(pattern, self.channelPath)

    def GetSubscribePath(self):
        pattern = r"\{\w+\}"
        return re.sub(pattern, '+', self.channelPath)

    def GetPathParts(self):
        return self.channelPath.split("/")

    def Parameters(self):
        if 'parameters' in self.data:
            return self.data['parameters']
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
                deps.add('"%s"' % (resolver.GetHeader(p[1]['$ref'])))
        for chItem in self.data.values():
            for op in ['subscribe', 'publish']:
                if op in chItem:
                    if '$ref' in chItem[op]['message']:
                        deps.add('"%s"' % (resolver.GetHeader(chItem[op]['message']['$ref'])))
        return deps

    def PyGetIncludes(self, resolver):
        deps = set()
        for chItem in self.data.values():
            for op in ['subscribe', 'publish']:
                if op in chItem:
                    if '$ref' in chItem[op]['message']:
                        deps.add(resolver.IncludeStatement(chItem[op]['message']['$ref']))
        return deps

class ServerObject(BaseDict):

    def __init__(self, root, name, initialdata):
        super().__init__(root, initialdata)
        self.name = name

        if self.data['protocol'] != 'mqtt':
            raise NotImplementedError("{} is not a supported protocol".format(self.data))
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


class Trait(BaseDict):

    def __init__(self, root, initialdata):
        super().__init__(root, initialdata)

        if 'bindings' in initialdata and '$ref' in initialdata['bindings']:
            self.data['bindings'] = self.root.Resolve(initialdata['bindings']['$ref'])


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

class Components(BaseDict):

    def __init__(self, root, initialdata):
        super().__init__(root, initialdata)


class SpecRoot(BaseDict):
    
    def __init__(self, initialdata, loader=None):
        super().__init__(self, initialdata)
        self.loader = loader

        if self.data['asyncapi'] != '2.0.0':
            raise NotImplementedError

        if 'channels' in self.data:
            self.data['channels'] = Channels(self, self.data['channels'])

        if 'components' in self.data:
            self.data['components'] = Components(self, self.data['components'])

        if 'servers' in self.data:
            self.data['servers'] = Servers(self, self.data['servers'])

    def Resolve(self, ref, asClass=None, **kwargs):
        theFile, thePath = ref.split('#')
        if len(theFile) > 0:
            if self.loader is not None:
                otherRoot = self.loader.Load(theFile)
                struct = otherRoot.Resolve("#"+thePath)
                if asClass is not None:
                    return asClass(otherRoot, struct, **kwargs)
                return struct
            raise NotImplementedError("No loader available for {}".format(theFile))
        else:
            pathParts = thePath.split('/')
            cur = self
            for part in [x for x in pathParts if x != '']:
                cur = cur[part]
            return cur