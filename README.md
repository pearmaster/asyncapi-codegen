# AsyncAPI Codegen

[![CircleCI](https://dl.circleci.com/status-badge/img/gh/pearmaster/asyncapi-codegen/tree/master.svg?style=shield)](https://dl.circleci.com/status-badge/redirect/gh/pearmaster/asyncapi-codegen/tree/master)

`asyncapi-codegen` interprets an AsyncAPI spec and generates code and documentation accordingly.   Only MQTT is supported.

There are two parts to this:

 * Interpret the AsyncAPI spec into Python classes in ways that makes it easier to use.
 * Use Jinja2 templates to create the code.

### Terminology

With pub/sub architecture, the broker is a server and everything is a client to it.  As such, is is useful to define the general nature of clients to differentiate roles between clients.

A **provider** is the MQTT service that provides functionality. The AsyncAPI spec describes the behavior of the provider.
A **utilizer** is the MQTT client that consumes the functionality.  When the AsyncAPI spec uses "publish" and "subscribe" terms, it is the utilizer that does the described action.

## Supported Languages

| Lanaguage  | MQTT Library      | JSON Library    | JSON Schema Library              |
|------------|-------------------|-----------------|----------------------------------|
| C++        | Mosquitto Client  | rapidjson       | Built-in via json-schema-codegen |
| Python     | Paho MQTT         | Python built-in | None                             |
| C          | None              | None            | None                             |         

### Features

| Feature                       | Python     | C++ | C    |
|-------------------------------|------------|-----|------|
| Enforces JSON Schema          | No         | Yes | No   |

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

## Installation

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

## C Language Generation

This is a work in progress, and will likely never be full featured.

Currently, only C format topic strings are generated.

## Using Docker

### Utilizer code

To generate utilizer/client C++ code for an AsyncAPI spec, you could run this docker command, carefully adjusting the volume mounting to the directory containing the specs and the directory for the output.  

When the YAML uses the words "publish" and "subscribe", the utilizer will perform those MQTT actions.

```sh
docker run --rm -t \
    -v $(pwd)/examples:/specs \
    -v $(pwd)/output:/output \
    --user $UID:$GID \
    docker.io/pearmaster/asyncapi-codegen:latest \
        --yaml /specs/streetlights-mqtt.yml \
        --name Streetlights \
        --cpp
```

### Provider code

If you'd like instead to generate C++ code for the provider, you can append `--progtype provider` to the docker command to look like:

```sh
docker run --rm -t \
    -v $(pwd)/examples:/specs \
    -v $(pwd)/output:/output \
    --user $UID:$GID \
    docker.io/pearmaster/asyncapi-codegen:latest \
        --yaml /specs/streetlights-mqtt.yml \
        --name Streetlights \
        --cpp \
        --progtype provider
```

### Markdown documentation

This command will generate documentation for utilizers.  The entire spec is output in one big markdown file.  

```sh
docker run --rm -t \
    -v $(pwd)/examples:/specs \
    -v $(pwd)/output:/output \
    --user $UID:$GID \
    docker.io/pearmaster/asyncapi-codegen:latest \
        --yaml /specs/streetlights-mqtt.yml \
        --name Streetlights
        --markdown
```

## License

GPLv2
