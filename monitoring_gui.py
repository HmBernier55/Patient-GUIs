import tkinter as tk
from tkinter import ttk, filedialog
import PIL
from PIL import Image, ImageTk
import requests
import base64
import os

SERVER_URL = 'http://vcm-29733.vm.duke.edu:5000/'

# variable holding currently loaded patient data
curr_gui_pt = None
curr_med_img = None
curr_ecg_img = None


def med_recs_from_server():
    """Requests a list of all medical record numbers from the patient server.

    Sends a GET request to the "/medical_record_numbers" route of the patient
    server (see fp_server.py). This route returns a list of all medical record
    numbers registered in the patient database (empty list if no patients). The
    result is returned from the server as a JSON string, which is converted to
    a Python list before being returned.

    Returns:
        list of integers: all medical record numbers currently in the patient
            database
    """
    result = requests.get(SERVER_URL + '/medical_record_numbers')
    return result.json()


def pt_data_from_server(med_rec):
    """Requests data from a specific patient from the patient server.

    Sends a GET request to the "/patient_data/<med_rec>" route of the patient
    server (see fp_server.py). This route returns a dictionary containing the
    all of the current data for that patient (medical record number, name,
    heart rates, ECG images, and medical images). Checks that the medical
    record number passed in is not the empty string (corresponding to no input
    selected in the GUI dropdown list) before making the request.

    Args:
        med_rec (numeric str): Medical record number as a string (gathered
            from the GUI dropdown list in the code below)

    Returns:
        dict: dictionary mapping names of patient fields (medical record
            number, name, etc.) to their corresponding values. See the fields
            of the patient class in database-definition.py for more details on
            the data in this dictionary. Depending on the data stored on the
            server for the specified patient, some fields may be missing from
            the dictionary.
    """
    if med_rec == '':
        return 'Please select a medical record number from the dropdown list'
    result = requests.get(SERVER_URL + f'/patient_data/{med_rec}')
    return result.json()


def process_dropdown_list(in_list, message):
    """Formats a list for display in a GUI dropdown list.

    Processes a list to be displayed in a GUI dropdown list to give more
    information to the user. If the list is empty, a list containing a message
    that no data is available for the dropdown is returned. For use in multiple
    scenarios, the message is passed in as a parameter. Placement of the
    message in a list allows it to be easily displayed in the dropdown list.

    Args:
        in_list (list): list of options to be displayed in the dropdown
        message (str): message to be displayed in the dropdown if the input
            list is empty

    Returns:
        list: processed version of the input list for dropdown display
    """
    # provides message in dropdown if list is empty
    if len(in_list) == 0:
        return [message]
    return in_list


def display_datetime_str(dt_str):
    """Removes timezone info from a datetime string.

    Removes the final 4 characters from the input string, corresponding to the
    timezone information of the datetime strings stored in the patient
    database (It seems MongoDB stores datetimes as strings instead of datetime
    objects). This allow the datetime strings to be displayed in a way for
    fitting for the GUI.

    Args:
        dt_str (str): datetime information as string from patient database

    Returns:
        str: datetime str with timezone removed
    """
    # removes time zone info from datetime string
    return dt_str[:-4]


def create_med_options(med_im_list):
    """Generates a list of medical image options for the GUI dropdown list.

    Creates a list of options for user selection to be displayed in the GUI
    dropdown lists corresponding to the medical images of a patient. Since the
    medical image strings in the database are long image encoding strings that
    will not fit in the dropdown or be useful to the user, this list of options
    acts as a way of mapping the medical image strings to an easier to use
    index. The list is created is [1, 2, ..., n-1, n], where n is the number
    of medical images for the patient.

    Args:
        med_im_list (list): list of medical image strings for a patient as
            received from the patient server

    Returns:
        list: Medical image selection options for the GUI dropdown list. See
            format in description above
    """
    return list(range(1, len(med_im_list) + 1))


def create_ecg_options(timestamp_list):
    """Generates a list of ECG image options for the GUI dropdown list.

    As in the above function create_med_options, but for the ECG dropdown list.
    Instead of the numbers 1, 2, ..., n-1, n, the options are those numbers
    linked to the associated datetime string timestamps of the ECG upload to
    give historical information about when the ECG data was gathered for easier
    selection by the user.

    Args:
        timestamp_list (list): list of ECG timestamp strings for a patient as
            received from the patient server

    Returns:
        list: ECG image selection options for the GUI dropdown list.
            Format: [1 - <timestamp>, 2 - <timestamp>, ...,
                     (n-1) - <timestamp>, n - <timestamp>]
    """
    timestamps = list(map(display_datetime_str, timestamp_list))
    options = [f'{i + 1} - {timestamps[i]}' for i in range(len(timestamps))]
    return options


def get_img_index(img_label):
    """Gets the index corresponding to the image selected from a dropdown list.

    Processes the image label selected from the GUI dropdown list to get the
    index in ECG/medical image list of the desired ECG/medical image string.
    This function provides the mapping from display options created in the
    functions above to the actual image strings in the patient database. If no
    selection was chosen (empty string), or a patient has not been selected
    ("Please select a Patient"), the function returns False and a message
    describing the problem

    Args:
        img_label (str): Chosen option from the GUI dropdown list

    Returns:
        (int/boolean, str): tuple containing:
            int/boolean: index of the image string in the ECG/medical image
                list of the current patient if a valid image was selected,
                false otherwise
            str: message describing the result of the function
    """
    if img_label == '':
        return False, 'Please select an image from the dropdown list'
    if img_label == 'Please Select a Patient':
        return False, 'Please select a patient from the dropdown ' +\
                      'list at the top of the window'
    index = img_label[0]
    if not index.isnumeric():
        return False, 'No valid image selected from image dropdown list'
    return int(index) - 1, 'Image loaded successfully'


def download_b64_img_from_str(b64_str, filename):
    """Downloads a base64 encoded image from a string.

    Uses a base64 encoded image string to create an image file. In the GUI,
    these image strings are saved in the ECG/medical image lists of the
    requested patient dictionaries. These strings are generated by the patient
    GUI (see patient_gui.py).

    Args:
        b64_str (str): base64 encoded image string
        filename (str): name of file to save image as, JPEG format recommended
    """
    image_bytes = base64.b64decode(b64_str)
    with open(filename, 'wb') as f:
        f.write(image_bytes)


def create_img_path_filename(filename):
    """Modifies the filename to be saved in the monitoring image directory.

    Adds "monitoring_image_data/" to the beginning of the filename to save
    images accessed by the monitoring GUI in the monitoring image directory.

    Args:
        filename (str): filename of image to be accessed by monitoring GUI

    Returns:
        str: modified filename containing path to monitoring image directory
    """
    return f'monitoring_image_data/{filename}'


def main_window():
    """Creates the main window of the monitoring GUI.

    Uses the tkinter library to create the main window of the monitoring GUI.
    Functions defined below provide functions to the GUI components defined
    in this main window function. The monitoring GUI accesses the patient
    server to allow the user to view patient information (medical record
    number, name), the patient's latest ECG data, and historical medical and
    ECG images associated with the patient. See the README for more details on
    how to use this GUI.
    """

    def get_medical_records():
        """Gets a GUI-accessible list of medical record numbers from server.

        Uses the med_recs_from_server function to get a list of medical record
        numbers for all patients registered in the patient database inside the
        GUI definition. This list of medical record numbers is processed for
        dropdown list display and returned for use in the patient selection
        dropdown list.

        Returns:
            list: list of medical records from the patient server processed for
                dropdown list display
        """
        med_rec_list = med_recs_from_server()
        med_rec_msg = 'No medical record numbers in database'
        med_rec_result = process_dropdown_list(med_rec_list, med_rec_msg)
        return med_rec_result

    def retrieve_patient_cmd():
        """Patient retrival command for patient selection GUI button.

        Gets the selected medical record number from the patient selection
        dropdown list in the GUI and retrieves the patient data for the patient
        specified by that medical record number. The patient data is saved
        globally for access by other GUI functions. This patient data is
        passed into other functions to populate the relevant GUI fields with
        the correct patient information. This function is called when the
        "Retrieve Patient Data" button is pressed in the GUI.
        """
        med_rec = selected_pt.get()
        pt_data = pt_data_from_server(med_rec)

        # error message returned from server
        if type(pt_data) == str:
            update_status_message(pt_data)

        # patient data returned from server
        else:
            global curr_gui_pt
            curr_gui_pt = pt_data
            populate_patient_fields(pt_data)
            populate_medical_selection(pt_data)
            populate_ecg_selection(pt_data)
            selected_ecg.set('')
            selected_med_im.set('')
            ecg_hr.set('Calculated Heart Rate: Please Select ECG Data')
            ecg_time.set('Measurement Date: Please Select ECG Data')
            show_tk_image('Default-ECG-Image.jpg', 'ecg')
            show_tk_image('Default-Image.jpg', 'med')
            success_msg = f'Patient {med_rec} Data Successfully Updated'
            update_status_message(success_msg)

    def populate_patient_fields(pt_data):
        """Populates patient data fields and dropdown lists with patient info.

        Uses the patient data returned from the patient server to fill out
        fields in the GUI corresponding to the patient's medical record number,
        name, latest ECG data, list of medical images, and list of ECG data.
        Because patient data dictionaries may not have all of these fields when
        returned from the patient server, this function checks for the
        existence of these keys and only populates fields with data that is
        present.

        Args:
            pt_data (dict): Patient data from the server.
                See pt_data_from_server function for more details.
        """
        pt_med_rec.set(f'Medical Record Number: {pt_data["_id"]}')
        if 'name' in pt_data:
            pt_name.set(f'Name: {pt_data["name"]}')
        else:
            pt_name.set('Name: None Assigned')
        if 'heart_rates' and 'timestamps' and 'ecg_images' in pt_data:
            lat_ecg_hr.set('Latest Calculated Heart Rate: ' +
                           f'{pt_data["heart_rates"][-1]}')
            timestamp = display_datetime_str(pt_data["timestamps"][-1])
            lat_ecg_time.set('Measurement Date: ' +
                             f'{timestamp}')
            download_b64_img_from_str(pt_data['ecg_images'][-1],
                                      create_img_path_filename('latest_ecg'
                                                               '.jpg'))
            show_tk_image('latest_ecg.jpg', 'ecg_lat')
        else:
            lat_ecg_hr.set('Latest Calculated Heart Rate: No ECG Data '
                           'Available')
            lat_ecg_time.set('Measurement Date: No ECG Data Available')
            show_tk_image('Default-No-ECG-Image.jpg', 'ecg_lat')

    def populate_medical_selection(pt_data):
        """Populates dropdown list of medical images for the patient.

        Uses the patient data returned from the server to get a list of all
        of the base64-encoded medical images associated with the patient,
        generates dropdown selection options for those images, and updates
        the medical image dropdown list with the new options.

        Args:
            pt_data (dict): Patient data from the server.
                See pt_data_from_server function for more details.
        """
        if 'med_images' in pt_data:
            med_options = create_med_options(pt_data['med_images'])
        else:
            med_options = []
        med_msg = 'Patient has no medical images'
        med_result = process_dropdown_list(med_options, med_msg)
        med_im_dropdown['values'] = med_result

    def populate_ecg_selection(pt_data):
        """Populates dropdown list of ECG data for the patient.

        As in the populate_medical_selection function, but for the ECG data
        dropdown list.

        Args:
            pt_data (dict): Patient data from the server.
                See pt_data_from_server function for more details.
        """
        if 'timestamps' in pt_data:
            ecg_options = create_ecg_options(pt_data['timestamps'])
        else:
            ecg_options = []
        ecg_msg = 'Patient has no ECG measurements'
        ecg_result = process_dropdown_list(ecg_options, ecg_msg)
        ecg_dropdown['values'] = ecg_result

    def select_ecg_img_cmd():
        """ECG image display command for the ECG data selection button.

        Gets the selected historical ECG data from the ECG dropdown list in
        the GUI. Converts the cooresponding base64-encoded image string to
        an image file and displays the image in the GUI if the ECG dropdown
        selection is valid. If the selection is invalid, a message describing
        the issue is displayed. Also populates the ECG data fields with ECG
        data associated with the selected ECG measurement. This function
        runs when the "Get ECG Data" button is pressed.
        """
        ecg_label = selected_ecg.get()
        ecg_img_index, ecg_msg = get_img_index(ecg_label)
        if ecg_img_index is False:
            update_status_message(ecg_msg)
        else:
            img_filename = 'selected_ecg.jpg'
            b64_str = curr_gui_pt['ecg_images'][ecg_img_index]
            global curr_ecg_img
            curr_ecg_img = b64_str
            download_b64_img_from_str(b64_str,
                                      create_img_path_filename(img_filename))
            show_tk_image(img_filename, 'ecg')
            populate_selected_ecg_fields(ecg_img_index)
            update_status_message(ecg_msg)

    def populate_selected_ecg_fields(ecg_img_index):
        """Populates the ECG data fields with the selected ECG measurements.

        Accesses the ECG data (heart rate, timestamp of data upload) for the
        patient at the specified index and displays that information on the
        GUI. ECG data is displayed under the selected ECG image.

        Args:
            ecg_img_index (int): index of ECG data to display from patient
                list of ECG data
        """
        ecg_hr.set('Latest Calculated Heart Rate: ' +
                   f'{curr_gui_pt["heart_rates"][ecg_img_index]}')
        timestamp = curr_gui_pt["timestamps"][ecg_img_index]
        ecg_time.set('Measurement Date: ' +
                     f'{display_datetime_str(timestamp)}')

    def select_med_img_cmd():
        """Medical image display command for medical image selection button.

        Gets the selected historical medical image from the medical image
        dropdown list in the GUI. Converts the cooresponding base64-encoded
        image string to an image file and displays the image in the GUI if the
        medical image dropdown selection is valid. If the selection is invalid,
        a message describing the issue is displayed. This function runs when
        the "View Medical Image" button is pressed.
        """
        med_img_label = selected_med_im.get()
        med_img_index, med_img_msg = get_img_index(med_img_label)
        if med_img_index is False:
            update_status_message(med_img_msg)
        else:
            img_filename = 'selected_med.jpg'
            b64_str = curr_gui_pt['med_images'][med_img_index]
            global curr_med_img
            curr_med_img = b64_str
            download_b64_img_from_str(b64_str,
                                      create_img_path_filename(img_filename))
            show_tk_image(img_filename, 'med')
            update_status_message(med_img_msg)

    def show_tk_image(img_filename, img_type):
        """Displays an image in the GUI using the Pillow library.

        Displays the image specified by the input filename in the GUI. An
        "image type" flag controls where the image is displayed. If the image
        cannot be identified by the Pillow library, a default "invalid image"
        is displayed instead.

        Args:
            img_filename (str): filename of the image to display
            img_type (str): flag determing whether the image is displayed in
                the "latest ECG", "selected ECG" or "medical image" sections
                of the GUI
        """
        img_size = ecg_img_size if img_type != 'med' else med_img_size
        try:
            pil_image = Image.open(create_img_path_filename(img_filename))
        except PIL.UnidentifiedImageError:
            pil_image = Image.open(create_img_path_filename('Default-Invalid'
                                                            '-Image.jpg'))
        pil_image = pil_image.resize(img_size)
        tk_image = ImageTk.PhotoImage(pil_image)
        if img_type == 'ecg':
            ecg_image_label.configure(image=tk_image)
            ecg_image_label.image = tk_image
        elif img_type == 'ecg_lat':
            lat_ecg_image_label.configure(image=tk_image)
            lat_ecg_image_label.image = tk_image
        else:
            med_image_label.configure(image=tk_image)
            med_image_label.image = tk_image

    def save_ecg_img_cmd():
        """Command for saving the selected ECG image locally.

        Saves the currently displayed ECG image selected from the ECG dropdown
        list in the GUI. If no image is currently displayed, a message is shown
        in the GUI indicating this and no image is saved. The location and
        filename of the saved image is specified by the user via a file
        dialog box. The file must be saved as a JPEG image. This function runs
        when the "Save Current ECG Image" button in the GUI is pressed.
        """
        if curr_ecg_img is None:
            update_status_message('No ECG Image Selected')
        else:
            filename = filedialog.asksaveasfilename(defaultextension='.jpg',
                                                    filetypes=[('JPEG Image',
                                                                '*.jpg')],
                                                    initialfile='ecg_image')
            if filename and filename[-4:] == '.jpg':
                download_b64_img_from_str(curr_ecg_img, filename)
                update_status_message('ECG Image Saved')
            else:
                update_status_message('Saving cancelled')

    def save_med_img_cmd():
        """Command for saving the selected medical image locally.

        Saves the currently displayed medical image selected from the medical
        image dropdown list in the GUI. If no image is currently displayed, a
        message is shown in the GUI indicating this and no image is saved. The
        location and filename of the saved image is specified by the user via a
        file dialog box. The file must be saved as a JPEG image. This function
        runs when the "Save Current Medical Image" button in the GUI is
        pressed.
        """
        if curr_med_img is None:
            update_status_message('No Medical Image Selected')
        else:
            filename = filedialog.asksaveasfilename(defaultextension='.jpg',
                                                    filetypes=[('JPEG Image',
                                                                '*.jpg')],
                                                    initialfile='med_image')
            if filename and filename[-4:] == '.jpg':
                download_b64_img_from_str(curr_med_img, filename)
                update_status_message('Medical Image Saved')
            else:
                update_status_message('Saving cancelled')

    def get_update_info():
        """Updates GUI information with data from the server every 15 seconds.

        Makes requests to the server to get the latest list of medical record
        numbers in the server and updates to the currently selected patient's
        data. If no patient is currently selected, only the list of medical
        record numbers is updated. If new ECG data is available for the
        selected patient, this function automatically displays the ECG image
        and populates the ECG fields. This function runs every 15 seconds by
        calling itself after 15 seconds using the tkinter root.after() linked
        to the main window function.
        """
        pt_dropdown['values'] = get_medical_records()

        # only update pt info if patient is selected
        global curr_gui_pt
        if curr_gui_pt is not None:
            med_rec = curr_gui_pt['_id']
            pt_data = pt_data_from_server(med_rec)
            curr_gui_pt = pt_data
            populate_patient_fields(pt_data)
            populate_medical_selection(pt_data)
            populate_ecg_selection(pt_data)
            success_msg = 'Patient List and Current Patient Data Updated'
            update_status_message(success_msg)
        else:
            update_status_message('Patient List Updated')

        root.after(update_time, get_update_info)

    def update_status_message(message):
        """General function for updating the status message in the GUI.

        Updates the status message bar component of the GUI with the input
        message. This provides the user with information on their successful
        or incorrect use of the GUI and any problems that occur with patient
        data accessibilty or server communication.

        Args:
            message (str): message to display in the status message component
                of the GUI
        """
        status_msg.set(message)

    def exit_cmd():
        """Exit command for GUI

        Closes GUI window and deletes temporary images saved by GUI used to
        easily display images in the GUI. This function runs when the "Exit"
        button is pressed in the GUI.
        """
        # delete temporary images accessed by gui
        if os.path.exists(create_img_path_filename('latest_ecg.jpg')):
            os.remove(create_img_path_filename('latest_ecg.jpg'))
        if os.path.exists(create_img_path_filename('selected_ecg.jpg')):
            os.remove(create_img_path_filename('selected_ecg.jpg'))
        if os.path.exists(create_img_path_filename('selected_med.jpg')):
            os.remove(create_img_path_filename('selected_med.jpg'))
        root.destroy()

    root = tk.Tk()
    root.title("Patient Monitoring System Window")
    # root.geometry("1000x700")

    # ***** gui parameters *****
    med_img_size = (400, 300)
    ecg_img_size = (400, 250)
    right_img_row = 2
    right_img_colspan = 2
    separator_row = 2
    update_time = 15000  # 15 seconds
    # **************************

    # ***** gui title *****
    gui_title = ttk.Label(root, text="Patient Monitoring System",
                          font='TkDefaultFont 16 bold')
    gui_title.grid(column=0, row=0, padx=10, sticky='w')
    # *********************

    # ***** patient selection dropdown & button *****
    pt_select_label = ttk.Label(root,
                                text="Select Patient (by Medical Record"
                                     " Number): ",
                                font='TkDefaultText 12')
    pt_select_label.grid(column=0, columnspan=2, row=1, pady=20, sticky='e')

    selected_pt = tk.StringVar()
    pt_dropdown = ttk.Combobox(root, textvariable=selected_pt)
    pt_dropdown.grid(column=2, row=1)
    pt_dropdown['values'] = get_medical_records()
    pt_dropdown.state(['readonly'])

    pt_select_btn = ttk.Button(root, text="Retrieve Patient Data",
                               command=retrieve_patient_cmd)
    pt_select_btn.grid(column=3, row=1, sticky='w')

    separator = ttk.Separator(root, orient='horizontal')
    separator.grid(column=0, columnspan=6, row=separator_row, sticky='ew')
    # ************************************

    # ***** patient information display *****
    pt_data_label = ttk.Label(root, text="Patient Data",
                              font='TkDefaultFont 12 bold')
    pt_data_label.grid(column=0, row=separator_row+1, pady=10)

    pt_med_rec = tk.StringVar()
    pt_med_rec.set("Medical Record Number: Please Select a Patient")
    pt_med_rec_label = ttk.Label(root, textvariable=pt_med_rec,
                                 font='TkDefaultText 12')
    pt_med_rec_label.grid(column=0, row=separator_row+3, pady=10)

    pt_name = tk.StringVar()
    pt_name.set("Name: Please Select a Patient")
    pt_name_label = ttk.Label(root, textvariable=pt_name,
                              font='TkDefaultText 12')
    pt_name_label.grid(column=0, row=separator_row+4, pady=10)
    # ***************************************

    # ***** Medical Image display *****
    med_im_data_label = ttk.Label(root, text="Medical Image",
                                  font='TkDefaultFont 12 bold')
    med_im_data_label.grid(column=right_img_row, columnspan=right_img_row,
                           row=separator_row+1, pady=10)

    med_image = Image.open('monitoring_image_data/Default-Image.jpg')
    med_image = med_image.resize(med_img_size)
    tk_med_image = ImageTk.PhotoImage(med_image)
    med_image_label = ttk.Label(root, image=tk_med_image)
    med_image_label.image = tk_med_image
    med_image_label.grid(column=right_img_row, row=separator_row+2,
                         columnspan=right_img_colspan, rowspan=9, padx=20)
    # *****************************

    # ***** patient medical image data selection *****
    med_im_select_label = ttk.Label(root, text="Select Medical Image: ",
                                    font='TkDefaultText 10')
    med_im_select_label.grid(column=right_img_row+right_img_colspan,
                             row=separator_row+2, pady=10)

    selected_med_im = tk.StringVar()
    med_im_dropdown = ttk.Combobox(root, textvariable=selected_med_im,
                                   width=30)
    med_im_dropdown.grid(column=right_img_row+right_img_colspan,
                         row=separator_row+3, padx=20)
    med_im_dropdown['values'] = ['Please Select a Patient']
    med_im_dropdown.state(['readonly'])

    med_im_select_btn = ttk.Button(root, text="View Medical Image",
                                   command=select_med_img_cmd)
    med_im_select_btn.grid(column=right_img_row+right_img_colspan,
                           row=separator_row+4, padx=10)

    med_im_save_btn = ttk.Button(root, text="Save Current Medical Image",
                                 command=save_med_img_cmd)
    med_im_save_btn.grid(column=right_img_row+right_img_colspan,
                         row=separator_row+5, padx=10)
    # ***********************************************

    # ***** Latest ECG Data display *****
    lat_ecg_data_label = ttk.Label(root, text="Latest ECG Data",
                                   font='TkDefaultFont 12 bold')
    lat_ecg_data_label.grid(column=0, row=separator_row+11, pady=10)

    lat_ecg_image = Image.open('monitoring_image_data/'
                               'Default-Patient-Image.jpg')
    lat_ecg_image = lat_ecg_image.resize(ecg_img_size)
    tk_lat_ecg_image = ImageTk.PhotoImage(lat_ecg_image)
    lat_ecg_image_label = ttk.Label(root, image=tk_lat_ecg_image)
    lat_ecg_image_label.image = tk_lat_ecg_image
    lat_ecg_image_label.grid(column=0, row=separator_row+12, rowspan=6,
                             padx=20)

    lat_ecg_hr = tk.StringVar()
    lat_ecg_hr.set('Calculated Heart Rate: Please Select a Patient')
    lat_ecg_hr_label = ttk.Label(root, textvariable=lat_ecg_hr,
                                 font='TkDefaultText 10')
    lat_ecg_hr_label.grid(column=0, row=separator_row+19)

    lat_ecg_time = tk.StringVar()
    lat_ecg_time.set('Measurement Date: Please Select a Patient')
    lat_ecg_time_label = ttk.Label(root, textvariable=lat_ecg_time,
                                   font='TkDefaultText 10')
    lat_ecg_time_label.grid(column=0, row=separator_row+20)
    # *****************************

    # ***** Selected ECG Data display *****
    ecg_data_label = ttk.Label(root, text="Selected ECG Data",
                               font='TkDefaultFont 12 bold')
    ecg_data_label.grid(column=right_img_row, columnspan=right_img_colspan,
                        row=separator_row+11, pady=10)

    ecg_image = Image.open('monitoring_image_data/Default-ECG-Image.jpg')
    ecg_image = ecg_image.resize(ecg_img_size)
    tk_ecg_image = ImageTk.PhotoImage(ecg_image)
    ecg_image_label = ttk.Label(root, image=tk_ecg_image)
    ecg_image_label.image = tk_ecg_image
    ecg_image_label.grid(column=right_img_row, row=separator_row+12,
                         columnspan=right_img_colspan, rowspan=6, padx=20)

    ecg_hr = tk.StringVar()
    ecg_hr.set('Calculated Heart Rate: Please Select ECG Data')
    ecg_hr_label = ttk.Label(root, textvariable=ecg_hr,
                             font='TkDefaultText 10')
    ecg_hr_label.grid(column=right_img_row, columnspan=right_img_colspan,
                      row=separator_row+19)

    ecg_time = tk.StringVar()
    ecg_time.set('Measurement Date: Please Select ECG Data')
    ecg_time_label = ttk.Label(root, textvariable=ecg_time,
                               font='TkDefaultText 10')
    ecg_time_label.grid(column=right_img_row, columnspan=right_img_colspan,
                        row=separator_row+20)
    # *****************************

    # ***** patient ecg data selection *****
    ecg_select_label = ttk.Label(root, text="Select ECG Measurement: ",
                                 font='TkDefaultText 10')
    ecg_select_label.grid(column=right_img_row+right_img_colspan,
                          row=separator_row+12, pady=10)

    selected_ecg = tk.StringVar()
    ecg_dropdown = ttk.Combobox(root, textvariable=selected_ecg, width=30)
    ecg_dropdown.grid(column=right_img_row+right_img_colspan,
                      row=separator_row+13)
    ecg_dropdown['values'] = ['Please Select a Patient']
    ecg_dropdown.state(['readonly'])

    ecg_select_btn = ttk.Button(root, text="Get ECG Data",
                                command=select_ecg_img_cmd)
    ecg_select_btn.grid(column=right_img_row+right_img_colspan,
                        row=separator_row+14, padx=10)

    ecg_save_btn = ttk.Button(root, text="Save Current ECG Image",
                              command=save_ecg_img_cmd)
    ecg_save_btn.grid(column=right_img_row+right_img_colspan,
                      row=separator_row+15, padx=10)
    # **************************************

    # ***** status message display *****
    status_msg = tk.StringVar()
    status_msg.set("Status: Ready")
    status_label = ttk.Label(root, textvariable=status_msg,
                             font='TkDefaultText 10')
    status_label.grid(column=0, row=separator_row+21, pady=20, sticky='w')
    # ***********************************

    # ***** exit button *****
    exit_btn = ttk.Button(root, text="Exit", command=exit_cmd)
    exit_btn.grid(column=4, row=separator_row+21, padx=10, sticky='e')
    # ***********************

    root.after(update_time, get_update_info)
    root.mainloop()


if __name__ == '__main__':
    main_window()
