'''

Basic code generator for Twilio Kotlin extensions.

Invoked by calling `generate <DATAFILE.json> <OUTPUT_FILE.kt>`

DATAFILE is a description of:

{
    <package>: {
        <classname>: {
            "constructors": <constructor-list>,
            "children": <children-list>
        },
        ... classname ...
    },
    ... package ...
}

<package> is a package name under `com.twilio.twiml`
<classname> is a class under that package
<constructor-list> is a list of JSON lists. Each element of constructor-list represents a
    the argument list for a constructor for <classname>'s builder class. Each element of the
    argument list is in the format "<argname>:<argtype>".
<children-list> is a list of classnames, which are valid TwiML children of the given class.
A classname may be "classname", which is the name of the class within the same package;
or may be "package.classname", which specifies the class as a child of "package".


This script will produce a full kotlin file, TwilioExtensions.kt, suitable for copying into IntelliJ.

'''

import sys
import json

from collections import defaultdict
from collections import Counter
from collections import namedtuple
from io import StringIO

from pprint import pprint

def __main__():

    builders = json.load(open(sys.argv[1]))
    output_file = open(sys.argv[2], "w") if len(sys.argv) > 2 else sys.stdout
    output = StringIO()

    imports = []
    # Key-value mapping: Key = Builder to construct, value = list(arglist format)
    constructors = defaultdict(list)
    # Key = the child type, value = list of possible parent element types for that class
    # n.b. acceptors is an inverted version of "children" from the data file.
    acceptors = defaultdict(list)

    # Build out the constructors and acceptors dictionaries
    for package, types in builders.items():
        for typename, info in types.items():
            typespec = TypeSpec(package, typename)
            imports.append(importer(typespec))
            for constructor in info["constructors"]:
                constructors[typespec].append(constructor_argstrings(constructor))
            for acceptor in info["children"]:
                q = acceptor.split(".")
                if len(q) == 1:
                    acceptor_package, acceptor_class = package, q[0]
                else:
                    acceptor_package, acceptor_class = q
                acceptors[TypeSpec(acceptor_package, acceptor_class)].append(typespec)

    # Code fragments for the constructor functions and the extension functions
    # respectively
    constructor_code = []
    extension_code = []
    marked_class_code = []

    package_layout_code = defaultdict(list)

    # Build out the code fragments
    for typespec, _constructor in constructors.items():
        for argstrings in _constructor:
            package_layout_code[typespec.package].append(fun_constructor(typespec, argstrings.declare, argstrings.consume))
            constructor_code.append(fun_constructor(typespec, argstrings.declare, argstrings.consume))
            for acceptor in acceptors[typespec]:
                extension_code.append(fun_extension(typespec, acceptor, argstrings.declare, argstrings.consume))
        package_layout_code[typespec.package].append(class_marked_with_constructors(typespec, _constructor))
        marked_class_code.append(class_marked_with_constructors(typespec, _constructor))

    imports.sort()
    constructor_code.sort()
    extension_code.sort()
    marked_class_code.sort()

    for k, v in package_layout_code.items():
        v.sort()

    # Generate the code!

    # Imports go first
    print("package com.alphasights.kotlintwilio", file=output)
    print("\nimport com.twilio.twiml.TwiML", file=output)
    print("\n".join(imports) + "\n", file=output)

    # Boilerplate code and type aliases
    print(fmt_preamble(), file=output)

    # The DSLTwiML namespace
    print(fmt_dsl_definition(package_layout_code), file=output)

    # The extenions
    print("\n".join(extension_code)+ "\n", file=output)

    # Finally, a list of types that have been declared as a valid child,
    # but have not had code generated.
    missing = list(set(acceptors) - set(constructors))
    missing.sort()
    print("\n", file=output)
    print(f"/** MISSING: {missing} */", file=output)

    reformatted = refmt_kotlin(output.getvalue())
    output_file.write(reformatted)


def camel(a):
    ''' Produces a function name that corresponds to the given class name --
    the Twilio SDK produces a function `className` for a class `ClassName` '''
    return a[0].lower() + a[1:]


def importer(typespec):
    ''' Return an import string for the given package/typename '''
    package = typespec.package.strip()
    sep = "." if package else ""
    name = typespec.name
    return f"import com.twilio.twiml.{package}{sep}{name}"

def fun_constructor(typespec, declare, consume):
    ''' Build a constructor function for the given class '''
    sep = ", " if declare else ""
    return f"""
    inline fun {camel(typespec.name)}({declare}{sep}f: Takes<{typespec.dsl_builder}> = {{}}): {typespec.qualified} = {typespec.dsl_builder}({consume}).apply(f).build()
    """.strip()

def fun_class_marked_constructor(declare, consume):
    ''' Build a constructor function for the given class '''
    return f"""
    constructor ({declare}) : super({consume})
    """.strip()

def fun_extension(typespec, acceptor, declare, consume):
    ''' Build an extension to construct a child under the given parent class '''
    sep = ", " if declare else ""
    return f"""
    inline fun {acceptor.qualified}.Builder.{camel(typespec.name)}({declare}{sep}f: Takes<{typespec.dsl_builder}> = {{}}): {acceptor.qualified}.Builder = this.{camel(typespec.name)}({typespec.dsl_constructor}({consume}{sep}f))
    """.strip()

def class_marked_with_constructors(typespec, constructors):
    ''' Build a DSL-marked class to ensure TwiML verbs are appropriately restricted. '''

    constructor_code = "\n".join(fun_class_marked_constructor(i, j) for (i, j) in constructors)

    return f"""@TwimlMarker class {typespec.name} : {typespec.qualified}.Builder {{
        {constructor_code}
    }}
    """

def fmt_preamble():
    ''' The code after the import lines and before the DSL definition '''
    return """
typealias Takes<F> = F.() -> Unit
@DslMarker annotation class TwimlMarker
"""

def fmt_dsl_definition(package_layout):
    ''' The DSL definition itself '''

    lines = []
    for package, code_bits in package_layout.items():
        code = "\n".join(code_bits)
        if package:
            pp = package.title()
            value = f"""
            object {pp} {{
                {code}
            }}
            """
        else:
            value = f"""{code}\n"""
        lines.append(value)
    c = "\n".join(lines)

    return f"""
object DSLTwiML {{
{c}
}}"""

def constructor_argstrings(args):
    ''' Produce the argstrings for the type. Args is a list of strings formatted
    "<argname>:<argtype>". This will return a form suitable for declaring in a Kotlin function,
    and a form suitable for consuming that declared function.
    '''

    declare_argstrings = []
    consume_argstrings = []
    for arg in args:
        argname, argtype = arg.split(":")
        declare_argstrings.append(f"{argname}: {argtype}")
        consume_argstrings.append(f"{argname}")

    declare_argstring = ", ".join(declare_argstrings)
    consume_argstring = ", ".join(consume_argstrings)
    sep = (", " if declare_argstrings else "")

    return ArgString(declare_argstring, consume_argstring)


def refmt_kotlin(unformatted):
    ''' This is a bad kotlin reformatter, but it works for the code that this generator outputs. '''

    lines = [i.strip() for i in unformatted.split("\n")]
    lines_out = []

    indent_count = 0

    for line in lines:

        if line.endswith("}"):
            indent_count -= 1

        lines_out.append("    " * indent_count + line)

        if line.endswith("{"):
            indent_count += 1

    return "\n".join(lines_out)


class ArgString(namedtuple("ArgString", ("declare", "consume"))):
    pass


class TypeSpec(namedtuple("TypeSpec", ("package", "name"))):

    @property
    def qualified(self):
        sep = "." if self.package else ""
        return f"com.twilio.twiml.{self.package}{sep}{self.name}"

    @property
    def dsl_constructor(self):
        p = self.package.title()
        sep = "." if p else ""
        return f"DSLTwiML.{p}{sep}{camel(self.name)}"

    @property
    def dsl_builder(self):
        p = self.package.title()
        sep = "." if p else ""
        return f"DSLTwiML.{p}{sep}{self.name}"

if __name__ == "__main__":
    __main__()
