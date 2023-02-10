#!/usr/bin/python3 -tt
from constructs import Construct
from cdktf import App, Fn, TerraformStack, Testing
from imports.random import (
    RandomProvider,
    Integer as NumericResource,
    Password as StringResource,
    Shuffle as ListResource,
)
from imports.local import LocalProvider, File


def writeToFile(scope: Construct, name: str, value):
    filename = f"../../../{name}"
    if isinstance(value, list):
        File(scope, name, filename=filename, content=Fn.jsonencode(value))
    else:
        File(scope, name, filename=filename, content=str(value))


class SourceStack(TerraformStack):
    def __init__(self, scope: Construct, ns: str):
        super().__init__(scope, ns)

        RandomProvider(self, "random")
        LocalProvider(self, "local")

        self.numericResource = NumericResource(self, "int", min=0, max=6)
        self.stringResource = StringResource(self, "str", length=32)
        self.listResource = ListResource(
            self, "list", input=["a", "b", "c", "d", "e", "f"]
        )

        writeToFile(self, "originNum", self.numericResource.result)
        writeToFile(self, "originStr", self.stringResource.result)
        writeToFile(self, "originList", self.listResource.result)


class ConsumerStack(TerraformStack):
    def __init__(self, scope: Construct, ns: str, inputs: dict):
        super().__init__(scope, ns)

        RandomProvider(self, "random")
        LocalProvider(self, "local")

        self.numericResource = inputs.get("numericResource")
        self.numericValue = inputs.get("numericValue")

        self.stringResource = inputs.get("stringResource")
        self.stringValue = inputs.get("stringValue")

        self.listResource = inputs.get("listResource")
        self.listValue = inputs.get("listValue")

        numericValue = (
            inputs["numericResource"].result
            if inputs.get("numericResource")
            else inputs.get("numericValue", None)
        )
        if numericValue:
            writeToFile(self, f"{ns}Num", numericValue)

        stringValue = (
            inputs["stringResource"].result
            if inputs.get("stringResource")
            else inputs.get("stringValue", None)
        )
        if stringValue:
            writeToFile(self, f"{ns}Str", stringValue)

        listValue = (
            inputs["listResource"].result
            if inputs.get("listResource")
            else inputs.get("listValue", None)
        )
        if listValue:
            writeToFile(self, f"{ns}List", listValue)


app = Testing.stub_version(App(stack_traces=False))
src = SourceStack(app, "source")
passthrough = ConsumerStack(
    app,
    "passthrough",
    {
        "numericResource": src.numericResource,
        "stringResource": src.stringResource,
        "listResource": src.listResource,
    },
)

ConsumerStack(
    app,
    "sink",
    {
        "numericResource": passthrough.numericResource,
        "stringResource": passthrough.stringResource,
        "listResource": passthrough.listResource,
    },
)

fns = ConsumerStack(
    app,
    "fns",
    {
        # From one stack
        "numericValue": Fn.sum(
            [src.numericResource.result, src.numericResource.result]
        ),
        # From two stacks
        "stringValue": Fn.join(
            separator=",", value=[src.stringResource.result, src.stringResource.result]
        ),
    },
)

ConsumerStack(
    app,
    "functionOutput",
    {
        "numericValue": fns.numericValue,
        "stringValue": fns.stringValue,
    },
)


app.synth()
