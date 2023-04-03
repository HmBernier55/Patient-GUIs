import pytest


@pytest.mark.parametrize("filename, b64_string",
                         [("Default-Image.jpg",
                           "/9j/4AAQSkZJRgABAQEA")])
def test_file_to_b64_string(filename, b64_string):
    from patient_gui import file_to_b64_string
    b64str = file_to_b64_string(filename)
    assert b64str[0:20] == "/9j/4AAQSkZJRgABAQEA"
