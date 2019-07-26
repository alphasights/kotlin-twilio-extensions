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


This script will produce a full kotlin file, TwilioExtensions.kt, suitable for copying into IntelliJ.

'''

import sys
import json

from collections import defaultdict
from collections import Counter
from collections import namedtuple

from pprint import pprint

def __main__():

    builders = json.load(open(sys.argv[1]))
    output = open(sys.argv[2], "w") if len(sys.argv) > 2 else sys.stdout

    imports = []
    # Key-value mapping: Key = Builder to construct, value = list(arglist format)
    constructors = defaultdict(list)
    # Key = the child type, value = list of possible parent element types for that class
    # n.b. acceptors is an inverted version of "children" from the data file.
    acceptors = defaultdict(list)

    # The package name for the given type
    packages = defaultdict(str)

    # Build out the constructors and acceptors dictionaries
    for package, types in builders.items():
        for typename, info in types.items():
            imports.append(importer(package, typename))
            for constructor in info["constructors"]:
                constructors[typename].append(constructor_argstrings(constructor))
            for acceptor in info["children"]:
                acceptors[acceptor].append(typename)
            packages[typename] = package

    # Code fragments for the constructor functions and the extension functions
    # respectively
    constructor_code = []
    extension_code = []
    marked_class_code = []

    # Build out the code fragments
    for typename, _constructor in constructors.items():
        for argstrings in _constructor:
            constructor_code.append(fun_constructor(typename, argstrings.declare, argstrings.consume))
            for acceptor in acceptors[typename]:
                extension_code.append(fun_extension(typename, acceptor, argstrings.declare, argstrings.consume))
        marked_class_code.append(class_marked_with_constructors(typename, packages[typename], _constructor))

    imports.sort()
    constructor_code.sort()
    extension_code.sort()
    marked_class_code.sort()

    # Generate the code!

    # Imports go first
    print("package com.alphasights.kotlintwilio", file=output)
    print("\nimport com.twilio.twiml.TwiML", file=output)
    print("\n".join(imports) + "\n", file=output)

    # Boilerplate code and type aliases
    print(fmt_preamble(), file=output)

    # The TwilioBuilders constructor namespace
    print(fmt_constructors(constructor_code), file=output)

    # The extenions themselves
    print("\n".join(extension_code)+ "\n", file=output)

    # The Marked DSL classes
    print(fmt_marked_classes(marked_class_code), file=output)

    # Finally, a list of types that have been declared as a valid child,
    # but have not had code generated.
    missing = list(set(acceptors) - set(constructors))
    missing.sort()
    print("\n", file=output)
    print(f"/** MISSING: {missing} */", file=output)


def camel(a):
    ''' Produces a function name that corresponds to the given class name --
    the Twilio SDK produces a function `className` for a class `ClassName` '''
    return a[0].lower() + a[1:]


def importer(package, typename):
    ''' Return an import string for the given package/typename '''
    package = package.strip()
    return f"import com.twilio.twiml{package}.{typename}"

def fun_constructor(typename, declare, consume):
    ''' Build a constructor function for the given class '''
    sep = ", " if declare else ""
    return f"""
    inline fun {camel(typename)}({declare}{sep}f: Takes<{typename}.Builder> = {{}}): {typename} = {typename}.Builder({consume}).apply(f).build()
    """.strip()

def fun_class_marked_constructor(typename, declare, consume):
    ''' Build a constructor function for the given class '''
    return f"""
    constructor ({declare}): super({consume})
    """.strip()

def fun_extension(typename, acceptor, declare, consume):
    ''' Build an extension to construct a child under the given parent class '''
    sep = ", " if declare else ""
    return f"""
    inline fun {acceptor}.Builder.{camel(typename)}({declare}{sep}f: Takes<{typename}.Builder> = {{}}): {acceptor}.Builder = this.{camel(typename)}(TwilioBuilders.{camel(typename)}({consume}{sep}f))
    """.strip()

def class_marked_with_constructors(typename, package, constructors):
    ''' Build a DSL-marked class to ensure TwiML verbs are appropriately restricted. '''

    constructor_code = "\n            ".join(fun_class_marked_constructor(typename, i, j) for (i, j) in constructors)

    return f"""
    object {typename} {{
        @TwimlMarker class Builder : com.twilio.twiml{package}.{typename}.Builder {{
            {constructor_code}
        }}
    }}"""

def fmt_preamble():
    ''' The code after the import lines and before the constructors '''
    return """
typealias Takes<F> = F.() -> Unit
@DslMarker annotation class TwimlMarker
"""

def fmt_constructors(constructor_list):
    ''' The code after the preamble, and before the extensions '''
    c = "\n        " + "\n        ".join(constructor_list)
    return f"""
class TwilioBuilders {{

    companion object {{{c}

    }}
}}
"""

def fmt_marked_classes(marked_class_list):
    ''' The code after the extensions, representing DSL-marked versions of the classes '''
    c = "\n        " + "\n        ".join(marked_class_list)

    return f"""
object Marked {{{c}
}}
    """


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


class ArgString(namedtuple("ArgString", ("declare", "consume"))):
    pass

if __name__ == "__main__":
    __main__()
