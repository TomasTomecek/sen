# -*- coding: utf-8 -*-


import pytest

from sen.tui.commands.base import Command, Argument, Commander, register_command, Option


@register_command
class MyCommand(Command):
    name = "test"
    description = "test desc"
    argument_definitions = [
        Argument("test-arg", "test-arg desc", aliases=["x"])
    ]

    def run(self):
        return 42


@register_command
class MyCommand2(Command):
    name = "test2"
    description = "test desc 2"
    argument_definitions = [
        Argument("test-arg", "test-arg desc", aliases=["x"]),
        Argument("test-arg2", "test-arg2 desc", default="banana"),
    ]
    option_definitions = [
        Option("test-opt", "test-opt desc")
    ]

    def run(self):
        return 42


def test_command_class():
    c = Command()
    assert c.arguments is None
    c.process_args([])
    assert c.arguments is not None
    with pytest.raises(AttributeError):
        print(c.arguments.not_there)
    with pytest.raises(NotImplementedError):
        c.run()


def test_custom_command():
    c = MyCommand()
    c.process_args(["x"])
    assert c.arguments.test_arg is True
    assert c.run() == 42


def test_arg_and_opt():
    c = MyCommand2()
    c.process_args(["x", "y"])
    assert c.arguments.test_arg is True
    assert c.arguments.test_opt == "y"
    assert c.run() == 42


def test_default_arg():
    c = MyCommand2()
    c.process_args([])
    assert c.arguments.test_arg2 == "banana"
    assert c.run() == 42


def test_opt():
    c = MyCommand2()
    c.process_args(["y"])
    assert c.arguments.test_arg is None
    assert c.arguments.test_opt == "y"
    assert c.run() == 42


def test_commander():
    com = Commander(None, None)
    c = com.get_command("test test-arg")
    assert c.arguments.test_arg is True
    assert c.run() == 42
