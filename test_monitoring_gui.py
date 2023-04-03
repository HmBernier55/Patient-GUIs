import pytest


@pytest.mark.parametrize("in_list, msg, expected",
                         [([], 'No medical record numbers in database',
                           ['No medical record numbers in database']),
                          ([1], 'No medical record numbers in database', [1]),
                          ([1, 3], 'No medical record numbers in database',
                           [1, 3])],
                         ids=['Empty list', 'Singleton', 'Multiple numbers'])
def test_process_dropdown_list(in_list, msg, expected):
    from monitoring_gui import process_dropdown_list

    result = process_dropdown_list(in_list, msg)
    assert result == expected


@pytest.mark.parametrize("in_str, expected",
                         [('Sat, 03 Dec 2022 7:35:30 GMT',
                           'Sat, 03 Dec 2022 7:35:30')],
                         ids=['Correct datetime str display'])
def test_display_datetime_str(in_str, expected):
    from monitoring_gui import display_datetime_str

    result = display_datetime_str(in_str)
    assert result == expected


@pytest.mark.parametrize("in_list, expected",
                         [([], []), (['test1'], [1]),
                          (['test1', 'test2'], [1, 2])],
                         ids=['Empty list', 'Singleton', 'Multiple strings'])
def test_create_med_options(in_list, expected):
    from monitoring_gui import create_med_options

    result = create_med_options(in_list)
    assert result == expected


@pytest.mark.parametrize("in_list, expected",
                         [([], []),
                          (['Sat, 03 Dec 2022 7:35:30 GMT'],
                           ['1 - Sat, 03 Dec 2022 7:35:30']),
                          (['Sat, 03 Dec 2022 7:35:30 GMT',
                            'Sat, 04 Dec 2022 7:35:30 GMT'],
                           ['1 - Sat, 03 Dec 2022 7:35:30',
                            '2 - Sat, 04 Dec 2022 7:35:30'])],
                         ids=['Empty list', 'Singleton', 'Multiple dates'])
def test_create_ecg_options(in_list, expected):
    from monitoring_gui import create_ecg_options

    result = create_ecg_options(in_list)
    assert result == expected


@pytest.mark.parametrize("label, expected_index, expected_msg",
                         [('', False,
                           'Please select an image from the dropdown list'),
                          ('Please Select a Patient', False,
                           'Please select a patient from the dropdown '
                           'list at the top of the window'),
                          ('Patient has no ECG measurements', False,
                           'No valid image selected from image dropdown list'),
                          ('a - Sat, 03 Dec 2022 7:35:30', False,
                           'No valid image selected from image dropdown list'),
                          ('1 - Sat, 03 Dec 2022 7:35:30', 0,
                           'Image loaded successfully')],
                         ids=['Empty string', 'Select a patient', 'No ECGs',
                              'Non-numeric', 'Valid'])
def test_get_img_index(label, expected_index, expected_msg):
    from monitoring_gui import get_img_index

    result = get_img_index(label)
    assert result[0] == expected_index
    assert result[1] == expected_msg


@pytest.mark.parametrize("filename, out_filename",
                         [('images/acl1.jpg', 'images/test_acl1.jpg')],
                         ids=['File successfully decoded from b64'])
def test_download_b64_img_from_str(filename, out_filename):
    from monitoring_gui import download_b64_img_from_str
    import base64
    import filecmp
    import os

    with open(filename, "rb") as image_file:
        b64_bytes = base64.b64encode(image_file.read())
    b64_string = str(b64_bytes, encoding='utf-8')

    download_b64_img_from_str(b64_string, out_filename)
    answer = filecmp.cmp(filename, out_filename)
    os.remove(out_filename)
    assert answer


@pytest.mark.parametrize("filename, expected",
                         [('test_img.jpg',
                           'monitoring_image_data/test_img.jpg')],
                         ids=['Filename generated successfully'])
def test_create_img_path_filename(filename, expected):
    from monitoring_gui import create_img_path_filename

    result = create_img_path_filename(filename)
    assert result == expected
