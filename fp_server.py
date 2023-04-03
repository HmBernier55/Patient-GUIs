from flask import Flask, request, jsonify
from datetime import datetime
from pymodm import connect, MongoModel, fields, errors as pymodm_errors
from database_definition import Patient
import ssl

app = Flask(__name__)


@app.route('/', methods=['GET'])
def server_status():
    """Server route indicating status of server.

    Server route at base server URL indicating that the server is running.

    Returns:
        str: message indicating server is on
    """
    return "Patient monitoring server is on"


def init_server(testing=True):
    """Server initialization function.

    Initializes server by connecting to the MongoDB for this project. The
    current database is cleared with each run to ensure no data is accidentally
    added during testing. Adds initial patients with base64 encoded image
    strings for ECG and medical image fields to the server for use in GUI
    development. If flag "testing" is True, additional patients are added with
    nonsense image strings that are short to make testing easier.


    Args:
        testing (bool, optional): Flag indicating whether to add
            ease-of-testing patients to database. Defaults to True.
    """
    connect("mongodb+srv://Hmbernier55:Futbol10!@bme547.fatrsol.mongodb.net/"
            "fp_database?retryWrites=true&w=majority",
            ssl_cert_reqs=ssl.CERT_NONE)
    # clear database to ensure known initialization state upon initialization
    for pt in Patient.objects.raw({}):
        pt.delete()

    if testing:
        add_patient(1, 'test1', 100, 'test1_ecg', 'test1_img')
        add_patient(2, 'test2', 200, 'test2_ecg', 'test2_img')

    with open('test_pt_b64_strings/pt_98_ecg.txt', 'r') as f:
        ecg_str_98 = f.read()
    with open('test_pt_b64_strings/pt_98_med.txt', 'r') as f:
        med_str_98 = f.read()
    add_patient(98, 'img_test_98', 111, ecg_str_98, med_str_98)

    with open('test_pt_b64_strings/pt_99_ecg.txt', 'r') as f:
        ecg_str_99 = f.read()
    with open('test_pt_b64_strings/pt_99_med.txt', 'r') as f:
        med_str_99 = f.read()
    add_patient(99, 'img_test_99', 222, ecg_str_98, med_str_98)
    add_ecg_data(99, 333, ecg_str_99)
    add_med_img(99, med_str_99)


def add_patient(med_rec, name=None, heart_rate=None, ecg_str=None,
                img_str=None):
    """Adds a patient to the database.

    Adds a patient to the database with the given medical record number. Since
    only the medical record number is necessary to add a patient the other
    inputs are optional. If the name, heart rate, ECG image string, or medical
    image string are included, these fields are added after the patient is
    saved to the database with the given medical record number. Otherwise,
    those fields are left empty in the patient.

    Args:
        med_rec (int): medical record number of the patient to be added
        name (str, optional): patient name. Defaults to None.
        heart_rate (int, optional): heart rate value in bpm. Defaults to None.
        ecg_str (str, optional): base64 encoded image string for ECG trace
            image. Defaults to None.
        img_str (str, optional): base64 encoded image string for medical
            image. Defaults to None.

    Returns:
        Patient (see database_definition.py): Custom patient class object
            with fields updated based on input data as saved in database
    """
    new_pt = Patient(med_rec=med_rec)
    added_pt = new_pt.save()

    if name is not None:
        update_name(med_rec, name)
    if heart_rate is not None and ecg_str is not None:
        add_ecg_data(med_rec, heart_rate, ecg_str)
    if img_str is not None:
        add_med_img(med_rec, img_str)

    return added_pt


def find_pt(med_rec):
    """Finds patient in database specified by medical record number.

    Searches the database for a patient with the given medical record number.
    If this patient exists, the Patient class for that patient is returned.
    Otherwise, the function returns False.

    Args:
        med_rec (int): medical record number of the patient to be found

    Returns:
        Patient/bool: Patient class for patient if they exist, False otherwise
    """
    try:
        pt = Patient.objects.raw({'_id': med_rec}).first()
    except pymodm_errors.DoesNotExist:
        return False
    return pt


def update_name(med_rec, name):
    """Updates name of patient in database.

    Updates the name of the patient with the given medical record number to the
    input name. The old name of the patient, if there was one, is replaced by
    the new name. Since this function is only called after a new patient is
    saved in the add_patient function, the patient is guaranteed to exist.

    Args:
        med_rec (int): medical record number of the patient to be updated
        name (str): new name for patient
    """
    pt = find_pt(med_rec)
    pt.name = name
    pt.save()


def add_ecg_data(med_rec, heart_rate, ecg_str):
    """Adds ECG data to a patient in the database.

    Adds the given heart rate, base64 encoded ECG image string, and timestamp
    of upload to lists corresponding to this information within the patient
    data. If ECG data already exists, these values are appended to the proper
    lists. Since this function is only called after a new patient is saved in
    the add_patient function, the patient is guaranteed to exist.

    Args:
        med_rec (int): medical record number of the patient to be updated
        heart_rate (int): calculated heart rate in bpm
        ecg_str (str): base64 encoded image string for ECG trace image
    """
    pt = find_pt(med_rec)
    pt.heart_rates.append(heart_rate)
    pt.ecg_images.append(ecg_str)
    pt.timestamps.append(datetime.now())
    pt.save()


def add_med_img(med_rec, img_str):
    """Adds medical image data to a patient in the database.

    Adds base64 encoded medical image string to medical image string list in
    the patient data. If medical image data already exists, this string is
    appended to medical image string list. Since this function is only called
    after a new patient is saved in the add_patient function, the patient is
    guaranteed to exist.

    Args:
        med_rec (int): medical record number of the patient to be updated
        med_str (str): base64 encoded image string for medical image
    """
    pt = find_pt(med_rec)
    pt.med_images.append(img_str)
    pt.save()


# ************************** Zac *********************************

@app.route('/medical_record_numbers', methods=['GET'])
def get_medical_record_numbers():
    """Server route to get list of all medical record numbers in the database.

    GET handler to return a list of all medical record numbers in the database
    upon receiving a request to the /medical_record_numbers route.

    Returns:
        (str, int): JSON string containing list of medical record numbers and
            associated status code for request
    """
    med_rec_list, status_code = get_medical_record_numbers_worker()
    return jsonify(med_rec_list), status_code


def get_medical_record_numbers_worker():
    """Implements '/medical_record_numbers' GET handler.

    Called by '/medical_record_numbers' GET handler to return a list of all
    medical record numbers in the database. If no patients exist in the
    database, an empty list is returned.

    Returns:
        (list of int, int): list of medical record numbers in database and
            associated status code for request
    """
    med_rec_list = []
    for pt in Patient.objects.raw({}):
        med_rec_list.append(pt.med_rec)

    return med_rec_list, 200


@app.route('/patient_data/<medical_record_number>', methods=['GET'])
def get_patient_data(medical_record_number):
    """Server route to get patient data for a given medical record number.

    GET handler to return a dictionary of patient data for a given medical
    record number upon receiving a request to the
    '/patient_data/<medical_record_number>' route.
    *Note: If fields of the patient data are empty, they will not be included
    in the returned dictionary. This is handled by the monitoring GUI (see
    monitoring_gui.py for details).

    Args:
        medical_record_number (str): string containing medical record number
            as sent by the route address

    Returns:
        (str, int): JSON string containing dictionary of patient data and
            associated status code for request. See create_pt_data_dict for
            details on the dictionary structure.
    """
    patient_data, status_code = get_patient_data_worker(medical_record_number)
    return jsonify(patient_data), status_code


def get_patient_data_worker(medical_record_number):
    """Implements '/patient_data/<medical_record_number>' GET handler.

    Called by '/patient_data/<medical_record_number>' GET handler to return a
    dictionary of patient data for the patient with the given medical record
    number. The medical record number is first validated to ensure it has the
    correct format and then is associated with a patient in the database. See
    validate_medical_record_number for details on the validation process.
    Because the validation function checks that the medical record number is
    an numeric string and in the database, it is safe to cast the number to an
    int and find_pt is guaranteed to return a patient.

    Args:
        medical_record_number (str): string containing medical record number
            as sent by the route address

    Returns:
        (dict/string int): dictionary of patient data if medical record number
            has the correct format, otherwise message containing explanation of
            invalid format and associated status code for request. See
            create_pt_data_dict for details on the dictionary structure.
    """
    result = validate_medical_record_number(medical_record_number)
    if result is not True:
        return result, 400

    pt = find_pt(int(medical_record_number))
    pt_data = create_pt_data_dict(pt)
    return pt_data, 200


def validate_medical_record_number(medical_record_number):
    """Validates format of input for '/patient_data/<medical_record_number>'.

    Ensures that the medical record number string passed through the route
    '/patient_data/<medical_record_number>' is both a numeric string and
    corresponds to a patient in the database. If one of these conditions is not
    met, a message explaining the issue is returned and the worker function
    above fails the request with a status code of 400.

    Args:
        medical_record_number (str): string containing medical record number
            as sent by the route address

    Returns:
       bool/str: True if medical record number has the correct format,
            otherwise message containing explanation of invalid format
    """
    if not medical_record_number.isnumeric():
        return 'Medical record number must be a numeric string'

    if not find_pt(int(medical_record_number)):
        return f'Patient with medical record number {medical_record_number}' +\
                ' not in patient database'

    return True


def create_pt_data_dict(pt):
    """Converts a MongoModel patient object to a dictionary.

    Converts the fields of a Patient MongoModel object (see
    database-definition.py) from the database to a dictionary mapping the
    names of fields to their values. This is done using the PyModm to_son()
    method to convert the object to a SON object, and then convert that to a
    dictionary. The dictionary has the following structure:

    {
        'name': <str> (name of patient),
        '_id': <int> (medical record number of patient),
        'med_images': <list of str> (list of medical image encoding strings),
        'ecg_images': <list of str> (list of ECG image encoding strings),
        'heart_rates': <list of int> (list of heart rate values in bpm),
        'timestamps': <list of str> (list of timestamps for ECG uploads),
        '_cls': <str> (class of object, always 'database_definition.Patient')
    }

    Args:
        pt (Patient): Patient class as stored in database

    Returns:
        dict: dictionary of patient data with format described above
    """
    return pt.to_son().to_dict()


# ************************ Hunter ********************************

@app.route("/new_patient", methods=["POST"])
def add_new_patient_to_server():
    """Server route that adds new patient info to database

    The function takes in an input json dictionary from a POST
    request from a GUI, validates that the medical record number
    was input, and outputs a message saying that the patient
    information was added, updated, or an error occurred. If
    an error occurred, a status code of 400 is returned otherwise
    a status code of 200 is returned.

    Format for patient information dictionary:
    {
        "med_rec": <medical_record_integer>
        "name": <patient_name_string>
        "heart_rate": <heart_rate_integer>
        "ecg_str": <ecg_b64_string>
        "img_str": <image_b64_string>
    }

    Args:
        (json dictionary): dictionary of patient information

    Returns:
        string: a message saying the patient information was
            added to the database, information was updated, or
            detailing what error occurred
        string: status code, either 200 or 400
    """
    in_data = request.get_json()
    message, status_code = add_new_patient_worker(in_data)
    return message, status_code


def add_new_patient_worker(in_data):
    """Driver function for the route /new_patient

    The function validates that the input json dictionary is of
    the correct format, keys, and values, adds the patient information
    to the database with the input json dictionary, and outputs a message
    of success or failure when adding the patient information and a status
    code. If the patient already exists, the patient information that was
    sent from GUI is then updated within the database. Patient names are
    updated, while new ecg and medical images are added to the database.

    Args:
        in_data (json dictionary): a dictionary of patient information
            containing a medical record number and possible name, heart
            rate, ecg graph, and medical image

    Returns:
        string: message saying if the patient data was added successfully
            or failed and why
        int: status code either a 200 for success or a 400 for a failure
    """
    result = validate_new_patient(in_data)
    if result is not True:
        return result, 400
    if find_pt(in_data["med_rec"]) is False:
        add_patient(in_data["med_rec"],
                    in_data["name"],
                    in_data["heart_rate"],
                    in_data["ecg_str"],
                    in_data["img_str"])
        return "Patient was successfully added to the database", 200
    else:
        if in_data["name"] is not None:
            update_name(in_data["med_rec"], in_data["name"])
        if (in_data["heart_rate"] is not None and
                in_data["ecg_str"] is not None):
            add_ecg_data(in_data["med_rec"], in_data["heart_rate"],
                         in_data["ecg_str"])
        if in_data["img_str"] is not None:
            add_med_img(in_data["med_rec"], in_data["img_str"])
        return "Patient information was successfully updated", 200


def validate_new_patient(in_data):
    """Validates the input json dictionary

    The function takes in a json dictionary, tests that the medical
    record number is in the dictionary, tests that each key has the
    correct name, and tests that each value has the right data type.
    If any of these fail, a message detailing the error is returned,
    otherwise the boolean True is returned.

    Args:
        in_data (json dictionary): a dictionary of patient information

    Returns:
        string or boolean: returns a string message if one of the
            validation tests fails and returns a boolean if they
            all pass
    """
    if in_data["med_rec"] is None:
        return "A medical record number must be entered"
    expected_keys = ["med_rec", "name", "heart_rate", "ecg_str",
                     "img_str"]
    expected_types = [int, str, int, str, str]
    for ex_key, ex_type in zip(expected_keys, expected_types):
        if ex_key not in in_data:
            return "Key {} is missing from POST data".format(ex_key)
        if (in_data[ex_key] is not None and type(in_data[ex_key])
                is not ex_type):
            return "Key {}'s value has the wrong data type".format(ex_key)
    return True


if __name__ == '__main__':
    init_server(testing=False)
    app.run(host="0.0.0.0")
