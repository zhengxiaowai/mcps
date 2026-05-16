from hello import greet


def test_greet_with_name():
    result = greet("Alice")
    assert result == "Hello, Alice!"


def test_greet_default():
    result = greet()
    assert result == "Hello, world!"
