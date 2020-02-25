import os
import jinja2
import stringcase
import re

PLANTUML_REPLACE = re.compile(r"```plantuml\n(.*)```", re.DOTALL|re.MULTILINE)

class Generator(object):

    def __init__(self, templatePkg, outputDir):
        self.templatePkg = templatePkg
        self.outputDir = outputDir
        self.generatedFiles = []
        self.jinjaEnvironment = None

    def GetJinjaEnvironment(self):
        def IsOfType(obj, theType):
            return theType in str(type(obj))

        def ReferencePointsToObject(ref):
            val = False
            if hasattr(ref, 'ref') and hasattr(ref, 'Resolve'):
                resolved = ref.Resolve()
                if hasattr(resolved, 'type'):
                    return resolved.type == 'object'
            return val

        def Bold(s: str):
            if s and s is not None and s != 'None' and len(s) > 0:
                return "**%s**" % (s)
            else:
                return ''

        def Italics(s: str):
            if s and s is not None and s != 'None' and len(s) > 0:
                return "_%s_" % (s)
            else:
                return ''

        def CppLineEnd(s: str):
            s = str(s)
            if s and s is not None and s != 'None' and len(s) > 0:
                return "%s;" % (s)
            else:
                return ''

        def BlockQuote(s: str, level=1):
            lines = str.split("\n")
            return "\n".join([">"+l for l in lines])

        def AddLeadingUnderscore(s: str):
            return "_%s" % (s)

        def Privatize(s: str):
            return AddLeadingUnderscore(stringcase.camelcase(s))

        def QuoteIfString(s: str, condition):
            if condition == 'string' or condition is True or isinstance(condition, str):
                return '"%s"' % (s)
            return s

        def Enumify(s: str):
            if s[0].isnumeric():
                s = '_'+s
            return stringcase.constcase(s)

        def Strip(s: str, chars):
            return s.strip(chars)

        def MdIndent(s: str, width: int):
            indention = " " * width
            newline = "\n"
            s += newline  # this quirk is necessary for splitlines method
            lines = s.splitlines()
            rv = lines.pop(0)
            if lines:
                rv += newline + newline.join(
                    indention + line if (line and not line.strip().startswith('<')) else line for line in lines
                )

            return rv

        def Doxygenify(s: str):
            if "```plantuml" in s:
                return PLANTUML_REPLACE.sub(r"\\startuml\n\1\\enduml", s)
            return s

        if self.jinjaEnvironment is None:
            #env = jinja2.Environment(loader=jinja2.PackageLoader(self.templatePkg, ''))
            loader = jinja2.ChoiceLoader([
                jinja2.PackageLoader(self.templatePkg, ''),
                jinja2.FileSystemLoader(searchpath="./templates/cpp"),
                jinja2.PackageLoader('asyncapicodegen.templates.cpp', ''),
                jinja2.PackageLoader('jsonschemacodegen.templates.cpp', ''),
                jinja2.PackageLoader('jsonschemacodegen.templates.markdown', ''),
            ])
            env = jinja2.Environment(loader=loader)
            env.filters['UpperCamelCase'] = stringcase.pascalcase
            env.filters['PascalCase'] = stringcase.pascalcase
            env.filters['CONST_CASE'] = lambda s : stringcase.constcase(str(s))
            env.filters['snake_case'] = stringcase.snakecase
            env.filters['camelCase'] = stringcase.camelcase
            env.filters['bold'] = Bold
            env.filters['italics'] = Italics
            env.filters['blockquote'] = BlockQuote
            env.filters['semicolon'] = CppLineEnd
            env.filters['type'] = type
            env.filters['underscore'] = AddLeadingUnderscore
            env.filters['quotestring'] = QuoteIfString
            env.filters['dir'] = dir # For debug
            env.filters['enumify'] = Enumify
            env.filters['privatize'] = Privatize
            env.filters['strip'] = Strip
            env.filters['mdindent'] = MdIndent
            env.filters['doxygen'] = Doxygenify
            env.tests['oftype'] = IsOfType
            env.tests['refToObj'] = ReferencePointsToObject
            self.jinjaEnvironment = env
        return self.jinjaEnvironment

    def RenderTemplate(self, template_name, output_name = None, **kwargs):
        output_filename = output_name or ".".join(template_name.split(".")[:-1])
        output_file = os.path.join(self.outputDir, output_filename)
        print("Creating %s" % (output_file))
        template = self.GetJinjaEnvironment().get_template(template_name)
        rendered = template.render(kwargs)
        with open(output_file, "w") as fp:
            fp.write(rendered)
        self.generatedFiles.append(output_filename)
