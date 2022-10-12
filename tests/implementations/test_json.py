from serialite import DeserializationSuccess, JsonSerializer


# no error checking, since data is assumed to be valid JSON
def test_valid_inputs():
    data = {"a": "Hello world", "b": 2}

    json_serializer = JsonSerializer()

    assert json_serializer.from_data(data) == DeserializationSuccess(data)
    assert json_serializer.to_data(data) == data
