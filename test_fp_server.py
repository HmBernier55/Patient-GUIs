import pytest
from datetime import datetime
from database_definition import Patient
from pymodm import errors as pymodm_errors


@pytest.mark.parametrize("med_rec, name, heart_rate, ecg_str, img_str",
                         [(3, 'test3', 300, 'test3_ecg', 'test3_img'),
                          (3, None, 300, 'test3_ecg', 'test3_img'),
                          (3, 'test3', None, 'test3_ecg', 'test3_img'),
                          (3, 'test3', 300, None, 'test3_img'),
                          (3, 'test3', 300, 'test3_ecg', None),
                          (3, None, None, None, None)],
                         ids=['All info', 'No name', 'No heart rate',
                              'No ECG', 'No medical image',
                              'Only medical record'])
def test_add_patient(med_rec, name, heart_rate, ecg_str, img_str):
    from fp_server import add_patient, init_server
    init_server()

    _ = add_patient(med_rec, name=name, heart_rate=heart_rate, ecg_str=ecg_str,
                    img_str=img_str)
    find_pt = Patient.objects.raw({'_id': med_rec}).first()
    find_pt.delete()

    assert find_pt.med_rec == med_rec

    if name is not None:
        assert find_pt.name == name
    if heart_rate is not None and ecg_str is not None:
        assert find_pt.heart_rates[-1] == heart_rate
        assert find_pt.ecg_images[-1] == ecg_str
    if img_str is not None:
        assert find_pt.med_images[-1] == img_str


@pytest.mark.parametrize("med_rec, expected",
                         [(1, Patient(med_rec=1, name='test1',
                          heart_rates=[100], ecg_images=['test1_ecg'],
                          med_images=['test1_img'])),
                          (3, False)],
                         ids=['Patient exists', 'Patient does not exist'])
def test_find_pt(med_rec, expected):
    from fp_server import find_pt, init_server
    init_server()
    assert find_pt(med_rec) == expected


@pytest.mark.parametrize("med_rec, name",
                         [(2, 'new_name')], ids=['Name updated'])
def test_update_name(med_rec, name):
    from fp_server import update_name, init_server
    init_server()

    update_name(med_rec, name)
    find_pt = Patient.objects.raw({'_id': med_rec}).first()
    assert find_pt.name == name


@pytest.mark.parametrize("med_rec, heart_rate, ecg_str",
                         [(2, 106, 'another_ecg_str')], ids=['ECG data added'])
def test_add_ecg_data(med_rec, heart_rate, ecg_str):
    from fp_server import add_ecg_data, init_server
    init_server()

    add_ecg_data(med_rec, heart_rate, ecg_str)
    find_pt = Patient.objects.raw({'_id': med_rec}).first()
    assert find_pt.heart_rates[-1] == heart_rate
    assert find_pt.ecg_images[-1] == ecg_str
    curr_time = datetime.now()
    time_delta = curr_time - find_pt.timestamps[-1]
    assert time_delta.seconds < 0.05


@pytest.mark.parametrize("med_rec, med_img_str",
                         [(2, 'another_img_str')], ids=['Medical image added'])
def test_add_med_img(med_rec, med_img_str):
    from fp_server import add_med_img, init_server
    init_server()

    add_med_img(med_rec, med_img_str)
    find_pt = Patient.objects.raw({'_id': med_rec}).first()
    assert find_pt.med_images[-1] == med_img_str

# **************************** Zac *************************************


# **********************************************************************
# **********************************************************************

@pytest.mark.parametrize("expected_list, expected_code",
                         [([1, 2, 98, 99], 200), ([1, 2, 98, 99, 3], 200),
                          ([], 200)],
                         ids=['Initial medical records returned',
                              'Medical records updated when patient added',
                              'No patients in database'])
def test_get_medical_record_numbers_worker(expected_list, expected_code):
    from fp_server import (get_medical_record_numbers_worker, init_server,
                           add_patient)
    init_server()
    if len(expected_list) > 4:
        _ = add_patient(3)
        med_rec_list, status_code = get_medical_record_numbers_worker()
        pt = Patient.objects.raw({'_id': 3}).first()
        pt.delete()
    elif len(expected_list) == 0:
        # clear database to test empty list return
        for pt in Patient.objects.raw({}):
            pt.delete()
        med_rec_list, status_code = get_medical_record_numbers_worker()
    else:
        med_rec_list, status_code = get_medical_record_numbers_worker()
    assert med_rec_list == expected_list
    assert status_code == expected_code


@pytest.mark.parametrize("med_rec, expected, expected_code",
                         [('3', 'Patient with medical record number 3 not in '
                                'patient database', 400),
                          ('1', {'name': 'test1', '_id': 1,
                                 'heart_rates': [100],
                                 'ecg_images': ['test1_ecg'],
                                 'med_images': ['test1_img']}, 200)],
                         ids=['Patient not in database',
                              'Patient in database'])
def test_get_patient_data_worker(med_rec, expected, expected_code):
    from fp_server import get_patient_data_worker, init_server
    init_server()
    result, status_code = get_patient_data_worker(med_rec)
    if type(result) == dict:
        assert result['name'] == expected['name']
        assert result['_id'] == expected['_id']
        assert result['heart_rates'] == expected['heart_rates']
        assert result['ecg_images'] == expected['ecg_images']
        assert result['med_images'] == expected['med_images']
    else:
        assert result == expected
    assert status_code == expected_code


@pytest.mark.parametrize("med_rec, expected",
                         [('hello',
                           'Medical record number must be a numeric string'),
                          ('3', 'Patient with medical record number 3 not in '
                                'patient database'),
                          ('1', True)],
                         ids=['Non-numeric medical record number',
                              'Patient not in database',
                              'Patient in database'])
def test_validate_medical_record_number(med_rec, expected):
    from fp_server import validate_medical_record_number, init_server
    init_server()
    result = validate_medical_record_number(med_rec)
    assert result == expected


@pytest.mark.parametrize("med_rec, expected",
                         [(1, {'name': 'test1', '_id': 1, 'heart_rates': [100],
                               'ecg_images': ['test1_ecg'],
                               'med_images': ['test1_img']}),
                          (2, {'name': 'test2', '_id': 2, 'heart_rates': [200],
                               'ecg_images': ['test2_ecg'],
                               'med_images': ['test2_img']})],
                         ids=['Patient 1 dict', 'Patient 2 dict'])
def test_create_pt_data_dict(med_rec, expected):
    from fp_server import create_pt_data_dict, init_server
    init_server()
    pt = Patient.objects.raw({'_id': med_rec}).first()
    pt_data_dict = create_pt_data_dict(pt)
    assert pt_data_dict['name'] == expected['name']
    assert pt_data_dict['_id'] == expected['_id']
    assert pt_data_dict['heart_rates'] == expected['heart_rates']
    assert pt_data_dict['ecg_images'] == expected['ecg_images']
    assert pt_data_dict['med_images'] == expected['med_images']


# *************************** Hunter ***********************************

@pytest.mark.parametrize("in_data, expected",
                         [({"med_rec": None,
                            "name": "Hunter",
                            "heart_rate": 100,
                            "ecg_str": "test_str",
                            "img_str": "test_str"},
                           "A medical record number must be entered"),
                          ({"med_rec": 1,
                            "name": "Hunter",
                            "heart_rate": 100,
                            "ecg_str": "test_str",
                            "img_str": "test_str"},
                           True),
                          ({"med_rec": "1",
                            "name": "Hunter",
                            "heart_rate": 100,
                            "ecg_str": "test_str",
                            "img_str": "test_str"},
                           "Key med_rec's value has the wrong data type"),
                          ({"med_rec": 1,
                            "name": "Hunter",
                            "ecg_str": "test_str",
                            "img_str": "test_str"},
                           "Key heart_rate is missing from POST data"),
                          ({"med_rec": 1,
                            "name": None,
                            "heart_rate": 100,
                            "ecg_str": "test_str",
                            "img_str": "test_str"},
                           True),
                          ({"med_rec": 1,
                            "name": "Hunter",
                            "heart_rate": None,
                            "ecg_str": "test_str",
                            "img_str": "test_str"},
                           True),
                          ({"med_rec": 1,
                            "name": "Hunter",
                            "heart_rate": 100,
                            "ecg_str": None,
                            "img_str": "test_str"},
                           True),
                          ({"med_rec": 1,
                            "name": "Hunter",
                            "heart_rate": 100,
                            "ecg_str": "test_str",
                            "img_str": None},
                           True)])
def test_validate_new_patient(in_data, expected):
    from fp_server import validate_new_patient
    answer = validate_new_patient(in_data)
    assert answer == expected


@pytest.mark.parametrize("in_data, expected_message, expected_code",
                         [({"med_rec": None,
                            "name": "Hunter",
                            "heart_rate": 100,
                            "ecg_str": "test_str",
                            "img_str": "test_str"},
                           "A medical record number must be entered",
                           400),
                          ({"med_rec": 4,
                            "name": "Hunter",
                            "heart_rate": None,
                            "ecg_str": None,
                            "img_str": None},
                           "Patient was successfully added to the database",
                           200),
                          ({"med_rec": 1,
                            "name": None,
                            "heart_rate": None,
                            "ecg_str": None,
                            "img_str": None},
                           "Patient information was successfully updated",
                           200)])
def test_add_new_patient_worker(in_data, expected_message, expected_code):
    from fp_server import add_new_patient_worker, init_server
    init_server()
    answer_message, answer_code = add_new_patient_worker(in_data)
    try:
        find_pt = Patient.objects.raw({'_id': 4}).first()
    except pymodm_errors.DoesNotExist:
        pass
    else:
        find_pt.delete()
    assert answer_message == expected_message, answer_code == expected_code
