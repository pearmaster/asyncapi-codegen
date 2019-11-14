# AsyncAPI Codegen

This 3rd-party open source tool creates C++ interfaces according to AsyncAPI specifications.  Currently, only MQTT is supported.

## Python Generator

The Python3 generator interprets a AsyncAPI specification and uses jinja2 templates to create a number of C++ sources and headers.

The AsyncAPI must be format-decoded first, using a JSON or YAML parser.  The resulting parsed structure is then passed to the generator.

The generator interprets the specification directly.  For example, if the specification defines a `publish` operation, the generator creates code for _publishing_.

#### Output files

The generator creates the following types of output files:

 * **client interface**.  This is the main interface for publishing or subscribing to messages.
 * **servers**.  Represents a connection to a server.   Currently, only _unauthenticated MQTT_ connections are supported.  A _server object_ is provided to a _client interface_ to establish the connection to the broker/server.
 * **parameters**.  These are just schema objects.
 * **messages**.  Currently, these are just schema objects.  However, in the future these objects will also take protocol-specific message bindings.
 * **schemas**. These are structures that always enforce schema compliance and provide (de-)serialization methods to rapidjson Value objects (which can thus be used to create JSON strings).

Generated code files should be annotated for **doxygen** document generation, or at least that is the goal.

### Installation

```sh
pip3 install asyncapi-codegen
```

### Python requirements for running code generator

See also [requirements.txt](./requirements.txt)

* python 3.7
* jinja2
* stringcase
* json-schema-codegen
* pyyaml


### C++ requirements for generated code

* boost (boost::optional and boost::variant among others)
* rapidjson
* C++11

## License

GPLv2