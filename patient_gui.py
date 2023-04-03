import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
from ecg_analysis import ecg_driver
import matplotlib.pyplot as plt
import requests
import base64
import os


ecg_filename = "Default-ECG-Image.jpg"
med_filename = "Default-Image.jpg"
avg_HR = None


def upload_data_to_server(med_rec, name, heart_rate,
                          ecg_str, img_str):
    """Uploads patient information to the server

    The function creates the json dictionary using the inputs to
    the function and makes a POST request to the virtual machine
    in order to add the patient data to the database. It receives
    a message detailing whether or not the POST request was
    successful or failed.

    Args:
        med_rec (string or int): the patient's medical record number
        name (string): the patient's name
        heart_rate (int): the calculated heart rate from the ecg graph
        ecg_str (string): b64 string of the ecg graph image
        img_str (string): b64 string of the medical image

    Returns:
        (string): message detailing if the POST request was successful
            or failed
    """
    out_data = {"med_rec": med_rec,
                "name": name,
                "heart_rate": heart_rate,
                "ecg_str": ecg_str,
                "img_str": img_str}
    r = requests.post("http://vcm-29733.vm.duke.edu:5000/new_patient",
                      json=out_data)
    return r.text


def file_to_b64_string(filename):
    """Converts an image file to a b64 string

    The function takes an input image and converts it to
    a unique b64 string. The function then outputs this string.

    Args:
        filename (string): the name of the image file

    Returns:
        string: b64 string of the input image
    """
    with open(filename, "rb") as image_file:
        b64_bytes = base64.b64encode(image_file.read())
    b64_string = str(b64_bytes, encoding='utf-8')
    return b64_string


def main_window():
    """Creates the window of the patient GUI

    The function contains multiple functions and tkinter
    buttons and labels in order to create a GUI for inputting
    patient information. The GUI allows the user to upload a
    medical record number, name, heart rate, ecg graph, and
    medical image to a database. See the README.md file for
    further instructions on how to use the GUI.

    Returns:
        GUI: a graphical user interface to input patient data
    """
    def image_resizing(filename):
        """Resizes an image for placement on a GUI

        The function takes an input filename of an image,
        resizes the x dimension of the image based on a
        y dimension size of 200 pixels, and outputs the
        tkinter image.

        Args:
            filename (string): name of the image file

        Returns:
            object: a tkinter image object
        """
        med_image = Image.open("{}".format(filename))
        x_size, y_size = med_image.size
        new_y = 200
        new_x = new_y * x_size/y_size
        med_image = med_image.resize((round(new_x), round(new_y)))
        tk_image = ImageTk.PhotoImage(med_image)
        return tk_image

    def med_image_button_cmd():
        """Controls the upload medical image button

        The function controls the upload medical image
        button to where whenever someone clicks the button
        it asks the user to pick a medical image file,
        resizes the image, and replaces the current image that
        is in the medical image label of the GUI.
        """
        global med_filename
        new_file = filedialog.askopenfilename()
        if new_file == "":
            return
        med_filename = new_file
        tk_image = image_resizing(new_file)
        med_image_label.configure(image=tk_image)
        med_image_label.image = tk_image

    def ecg_image_button_cmd():
        """Controls the upload ecg graph button

        The function controls the upload ecg graph button.
        Whenever someone clicks the button, it asks the user to select
        a csv file of ecg data, calculates the heart rate of the data,
        plots the data, resizes the ecg graph to fit on the GUI, and
        displays the heart rate and ecg graph on the GUI.
        """
        global ecg_filename, avg_HR
        new_file = filedialog.askopenfilename()
        if new_file == "":
            return
        time, volt, heart_rate = ecg_driver(new_file)
        avg_HR = heart_rate
        if os.path.exists("ECG_graph.jpg"):
            os.remove("ECG_graph.jpg")
        ecg_plotting(time, volt)
        tk_image = image_resizing("ECG_graph.jpg")
        ecg_image_label.configure(image=tk_image)
        ecg_image_label.image = tk_image
        heart_rate_string = str(heart_rate)
        heart_rate_value_label.configure(text=heart_rate_string)
        ecg_filename = "ECG_graph.jpg"

    def ecg_plotting(time, voltage):
        """Plots the input ecg data

        The function takes in times and voltages from a csv
        file of ecg data, plots the data, labels the axes of
        the graph, saves the figure, and clears the memory of
        the plot for whenever the function needs to be called again.
        This is to avoid plots overlapping on one plot whenever
        multiple ecg data files are being evaluated.

        Args:
            time (list of floats): list of time values
            voltage (list of floats): list of voltage values

        Returns:
            plot: a saved figure of the times and voltages
        """
        plt.figure()
        plt.plot(time, voltage)
        plt.xlabel("Time (s)")
        plt.ylabel("Voltage (mV)")
        plt.savefig("ECG_graph.jpg")
        plt.clf()
        plt.cla()

    def exit_cmd():
        """Controls the exit button

        The function controls the exit button on the GUI.
        Whenever the button is clicked, the GUI closes,
        the main_window loop ends, and the temporary ecg
        figure is deleted.
        """
        if os.path.exists("ECG_graph.jpg"):
            os.remove("ECG_graph.jpg")
        root.destroy()
        exit()

    def clear_cmd():
        """Controls the clear GUI button

        The function controls the clear GUI button.
        Whenever the button is clicked, the medical record number
        and name entry boxes clear, the heart rate resets to zero,
        the ecg graph and medical image labels get reset to the
        default image, and the status label is reset. This is all
        done without closing the GUI.
        """
        global ecg_filename, med_filename, avg_HR
        patient_id_entry.delete(0, 'end')
        patient_name_label.delete(0, 'end')
        med_image_label.configure(image=tk_image_med)
        med_filename = "Default-Image.jpg"
        ecg_image_label.configure(image=tk_image_ecg)
        ecg_filename = "Default-ECG-Image.jpg"
        if os.path.exists("ECG_graph.jpg"):
            os.remove("ECG_graph.jpg")
        heart_rate_value_label.configure(text="0")
        avg_HR = None
        status_label.configure(text="Status")

    def upload_button_cmd():
        """Controls the upload data button

        The function controls the upload data button on the GUI.
        Whenever the button is clicked, whatever information has
        been added to the GUI (i.e. medical record number,
        name, heart rate, ecg graph, or medical image) gets saved to
        a variable that is input into the upload data to server function.
        If any field within the GUI was not updated, the variable is
        set to None. Both ecg graph and medical image are converted
        to b64 strings using the file_to_b64_string function. Once
        the upload_data_to_server function is called, the function
        changes the status label to reflect the message output
        from the server on whether or not the POST request was
        successful.
        """
        if not patient_id_entry.get() or patient_id_entry.get() == 0:
            med_rec = None
        else:
            med_rec = patient_id_entry.get()
            try:
                med_rec = int(med_rec)
            except ValueError:
                med_rec = med_rec
        if not patient_name_entry.get():
            name = None
        else:
            name = patient_name_entry.get()
        ecg_b64_string = file_to_b64_string(ecg_filename)
        if ecg_b64_string[0:54] == ("/9j/4AAQSkZJRgABAQEAkACQ"
                                    "AAD/2wBDAAMCAgMCAgMDAwME"
                                    "AwMEBQg"):
            ecg_string = None
            heart_rate = None
        else:
            ecg_string = ecg_b64_string
            heart_rate = avg_HR
        med_b64_string = file_to_b64_string(med_filename)
        if med_b64_string[120:150] == ("2wBDAQMEBAUEBQkFB"
                                       "QkUDQsNFBQUFB"):
            img_string = None
        else:
            img_string = med_b64_string
        msg = upload_data_to_server(med_rec, name, heart_rate,
                                    ecg_string, img_string)
        status_label.configure(text=msg)

    def clear_med_image():
        """Controls the clear medical image button

        The function controls the clear medical image button
        on the GUI. Whenever the button is clicked, the medical
        image on the GUI is reset to the default image.
        """
        global med_filename
        med_image_label.configure(image=tk_image_med)
        med_filename = "Default-Image.jpg"

    def clear_ecg_graph():
        """Controls the clear ecg graph button

        The function controls the clear ecg graph button
        on the GUI. Whenever the button is clicked, the ecg
        graph image is reset to the default image, the heart
        rate label is reset to zero, and the temporary ecg
        graph figure is deleted.
        """
        global ecg_filename, avg_HR
        ecg_image_label.configure(image=tk_image_ecg)
        ecg_filename = "Default-ECG-Image.jpg"
        if os.path.exists("ECG_graph.jpg"):
            os.remove("ECG_graph.jpg")
        heart_rate_value_label.configure(text="0")
        avg_HR = None

    root = tk.Tk()
    # Beginning of Buttons
    root.title("Patient Database System Window")
    ttk.Label(root, text="Patient Database System").grid(column=0, row=0,
                                                         columnspan=2,
                                                         sticky="w")

    ttk.Label(root, text="Medical ID:").grid(column=0, row=1, sticky="e")
    patient_id = tk.StringVar()
    patient_id_entry = ttk.Entry(root, textvariable=patient_id)
    patient_id_entry.grid(column=1, row=1, sticky="w")

    ttk.Label(root, text="Name:").grid(column=0, row=2, sticky="e")
    patient_name_entry = tk.StringVar()
    patient_name_label = ttk.Entry(root, width=40,
                                   textvariable=patient_name_entry)
    patient_name_label.grid(column=1, row=2, sticky="w")

    ttk.Label(root, text="Heart Rate:").grid(column=0, row=3, sticky="e")
    heart_rate_value_label = ttk.Label(root, text="0")
    heart_rate_value_label.grid(column=1, row=3, sticky="w")

    ttk.Label(root, text="Medical Image", font=("Arial", 12,
                                                "bold")).grid(column=1, row=4)
    tk_image_med = image_resizing(med_filename)
    med_image_label = ttk.Label(root, image=tk_image_med)
    med_image_label.image = tk_image_med
    med_image_label.grid(column=1, row=5)

    ttk.Label(root, text="ECG Data", font=("Arial", 12,
                                           "bold")).grid(column=4, row=4)
    tk_image_ecg = image_resizing(ecg_filename)
    ecg_image_label = ttk.Label(root, image=tk_image_ecg)
    ecg_image_label.image = tk_image_ecg
    ecg_image_label.grid(column=4, row=5)

    ttk.Button(root, text="Load Image",
               command=med_image_button_cmd).grid(column=1, row=6)

    ttk.Button(root, text="Clear Image",
               command=clear_med_image).grid(column=1, row=7)

    ttk.Button(root, text="Load ECG Data",
               command=ecg_image_button_cmd).grid(column=4, row=6)

    ttk.Button(root, text="Clear Graph",
               command=clear_ecg_graph).grid(column=4, row=7)

    ttk.Button(root, text="Upload Data",
               command=upload_button_cmd).grid(column=2, row=8)

    ttk.Button(root, text="Clear GUI", command=clear_cmd).grid(column=3, row=8)

    ttk.Button(root, text="Exit", command=exit_cmd).grid(column=0, row=9)

    status_label = ttk.Label(root, text="Status")
    status_label.grid(column=5, row=9)

    root.mainloop()


if __name__ == '__main__':
    main_window()
