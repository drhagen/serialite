from serialite import JsonSerializer, Success


# no error checking, since data is assumed to be valid JSON
def test_valid_inputs():
    data = {"a": "Hello world", "b": 2}

    json_serializer = JsonSerializer()

    assert json_serializer.from_data(data) == Success(data)
    assert json_serializer.to_data(data) == data
