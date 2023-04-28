# AsyncAPI Codegen

`asyncapi-codegen` interprets an AsyncAPI spec and generates code and documentation accordingly.   Only MQTT is supported.

There are two parts to this:

 * Interpret the AsyncAPI spec into Python classes in ways that makes it easier to use.
 * Use Jinja2 templates to create the code.

## Supported Languages

| Lanaguage  | MQTT Library      | JSON Library    | JSON Schema Library              |
|------------|-------------------|-----------------|----------------------------------|
| C++        | Mosquitto Client  | rapidjson       | Built-in via json-schema-codegen |
| Python     | Paho MQTT         | Python built-in | None                             |

Features:

| Feature                       | Python     | C++ |
|-------------------------------|------------|-----|
| Enforces JSON Schema          | No         | Yes |

## Documentation Formats

Formats:

 * Markdown (with significant HTML), suitable for display on GitLab.
 

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

* python 3.10
* jinja2
* stringcase
* json-schema-codegen
* pyyaml

## Python Code Generation

### Requirements for the generated python code

* python 3.7
* parse
* paho-mqtt

## C++ Code Generation 

### Requirements for the generated C++ code

* boost (boost::optional and boost::variant among others)
* rapidjson 1.1
* C++11

## License

GPLv2
