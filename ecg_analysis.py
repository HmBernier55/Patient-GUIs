import matplotlib.pyplot as plt
import scipy.signal
import numpy as np
import json
import logging


def read_file(filename):
    """Reads in a csv file of data line by line

    The function receives a filename, logs that the analysis
    has begun, opens the csv file and reads it line by line,
    saves the values as list of strings, and closes the file.

    Args:
        filename (string): name of csv file

    Returns:
        list of strings: every line within the csv file
        string: name of csv file
    """
    data_file = open("{}".format(filename), 'r')
    in_lines = data_file.readlines()
    data_file.close()
    return in_lines


def format_data(in_lines):
    """Removes the \n formatting

    The function receives a list of lines from a csv file
    and removes the \n from the end of each time, voltage pair.

    Args:
        in_lines (list of strings): every line from csv file

    Returns:
        list of strings: every line of data from csv file
            without \n
    """
    new_data = []
    for ele in in_lines:
        new_data.append(ele.strip())
    return new_data


def separate_values(data):
    """Separates each time, voltage pair into their own string

    The function receives a list of lines from a csv file where
    each element is a single string of 'time, voltage' and
    separates each element into a list of two strings
    ['time', 'voltage'] using the split command and a delimiter
    of a ','.

    Args:
        data (list of strings): list of strings where each element is
            a single string

    Returns:
        list of lists of strings: list of strings where each element
            is a list of two strings
    """
    new_data = []
    for ele in data:
        new_data.append(ele.split(','))
    return new_data


def remove_bad_data(data):
    """Removes a 'time, voltage' pair if data is missing, contains a
        non-numeric string, or is NaN

    The function receives a list of strings that are 'time, voltage'
    pairs, loops through each pair and checks if it contains an
    alphabetic string or is missing. If this check comes back true,
    the function saves the index of the data pair and logs an error
    that the data point was skipped due to bad data. The index list
    of bad data is then looped through to remove all of the bad data
    from the inputted list of strings.

    Args:
        data (list of lists of strings): list containing 'time, voltage'
            pairs

    Returns:
        list of lists of strings: list containing 'time, voltage' pairs
            where the bad data has been removed
        log: error logs that a data point was removed
    """
    idx = []
    for c, ele in enumerate(data):
        for d, value in enumerate(ele):
            if any(x.isalpha() for x in value) or value == '':
                idx.append(c)
                break
    for index in sorted(idx, reverse=True):
        del data[index]
    return data


def time_volt_lists(new_data):
    """Breaks up the list of 'time, voltage' pairs into two lists

    The function receives a cleaned list of 'time, voltage' pairs
    and breaks them up into a list of times and a list of voltages.
    It then converts all the values in each list from strings to
    floats.

    Args:
        new_data (list of lists of strings): a list of cleaned
            'time, voltage' pairs

    Returns:
        (list of floats): list of time values in seconds
        (list of floats): list of voltage values in mV
    """
    time = []
    voltage = []
    for values in new_data:
        time.append(values[0])
        voltage.append(values[1])
    time = [float(x) for x in time]
    voltage = [float(y) for y in voltage]
    return time, voltage


def voltage_range(voltages, filename):
    """Checks the voltage range of the ecg data

    The function receives a list of voltages and the filename.
    It checks if any of the voltages in the list are above 300 mV
    or below -300 mV. If one of the voltages falls outside of
    this range, the function logs a warning to the user that
    the file being analyzed has voltage values outside of
    the normal range.

    Args:
        voltages (list of floats): list of voltage values in mV
        filename (string): name of the csv file being analyzed

    Returns:
        log: a warning is logged to the logging file
    """
    for ele in voltages:
        if ele > 300 or ele < -300:
            break


def BandPassFilter(signal):
    """Runs a bandpass filter over the voltage data

    The function receives a list of voltages and runs a bandpass
    filter over the inputted voltage data with cutoff frequencies
    at 1 Hz and 30 Hz. The bandpass filter was created using the
    scipy package command signal.butter which takes an order,
    a low and high frequency cutoff, and a specification of which
    filter. This filter is then run over the data using
    scipy.signal.filtfilt command.

    Args:
        signal (list of floats): list of voltage values in mV

    Returns:
        list of floats: list of newly filtered voltage values
            in mV
    """
    fs = 360
    lowcut = 1.0
    highcut = 30.0

    nyq = 0.5*fs
    low = lowcut/nyq
    high = highcut/nyq

    order = 2

    b, a = scipy.signal.butter(order, [low, high], 'bandpass', analog=False)
    y = scipy.signal.filtfilt(b, a, signal)

    return y


def duration_calc(time):
    """Calculates the duration of ecg signal

    The function receives a list of time values and calculates
    the duration of the ecg signal by subtracting the
    last time value from the first time value. It also logs
    that the duration is being calculated.

    Args:
        time (list of floats): list of time values in seconds

    Returns:
        float: the calculated duration in seconds
        log: an info log that the duration is being calculated

    """
    duration = time[-1]-time[0]
    return duration


def voltage_extremes(voltage):
    """Calculates the minimum and maximum voltage values

    The function receives a list of voltage values and
    determines the minimum and maximum voltage value using
    the min() and max() commands. It also logs that the min
    and max values are being calculated.

    Args:
        voltage (list of floats): list of voltage values in mV

    Returns:
        tuple: a tuple of the minimum and maximum voltage values
        log: an info log that the minimum and maximum voltage
            values are being calculated
    """
    max_volt = max(voltage)
    min_volt = min(voltage)
    extremes = (min_volt, max_volt)
    return extremes


def peak_find(time, voltage):
    """Finds the peaks and the times of the peaks in the ecg signal

    The function receives a list of time and voltage values and,
    with the help of the scipy package, determines the peaks of the
    ecg signal. The find_peaks command within the scipy package
    allows you to specify a relative distance and a relative prominence
    between which a peak can be determined. This command also saves
    the indices of the times that the determined peaks occur. These
    indices are used to determine the times of each peak. It also
    logs that the times of the peaks are being determined.

    Args:
        time (list of floats): list of time values in seconds
        voltage (list of floats): list of voltage values in mV

    Returns:
        list of floats: list of time values where peaks occur
        log: an info log that the times of the beats are being
            determined
    """
    peaks, _ = scipy.signal.find_peaks(voltage, distance=150,
                                       prominence=(0.6, None))
    beats = [time[x] for x in peaks]
    return beats


def num_beats(time_of_beats):
    """Calculates the number of beats in the ecg signal

    The function receives a list of time values that correspond
    to the peaks in ecg signal. Using this list, the number of beats
    is calculated using the length of the list. It also logs that
    the number of beats are being calculated.

    Args:
        time_of_beats (list of floats): list of times corresponding
            to the beats in ecg signal

    Returns:
        int: the number of beats in the ecg signal
        log: an info log that the number of beats is being
            calculated
    """
    beats = len(time_of_beats)
    return beats


def avg_HR(beat_num, duration):
    """Calculates the average heart rate in beats per minute (bpm)

    The function receives the number of beats and the duration of
    the ecg signal and calculates the average heart rate in bpm
    using the equation:
    Mean HR = (number of beats)/(duration in seconds)*60
    Multiplying the average heart rate by 60 converts it from
    beats per second to beats per minute. It also logs that the
    average heart rate is being calculated.

    Args:
        beat_num (int): number of beats in the ecg signal
        duration (float): duration of the ecg signal

    Returns:
        float: average heart rate in bpm
        log: an info log that the average heart rate is being
            calculated
    """
    mean_HR = beat_num/duration*60
    return mean_HR


def patient_dict(duration, extremes, beats_num, mean_HR, time_beats):
    """Creates a dictionary of information about the ecg signal

    The function receives the duration, the min and max voltages,
    the number of beats, the average heart rate, and the times that
    beats occur in the ecg signal. Using these values, it creates
    a dictionary called metrics.

    Args:
        duration (float): duration of the ecg signal
        extremes (tuple): min and max voltage values
        beats_num (int): number of beats in the ecg signal
        mean_HR (float): average heart rate in bpm
        time_beats (list of floats): list of times that beats occur

    Returns:
        dictionary: a dictionary of information about the ecg signal
    """
    metrics = {"duration": duration,
               "voltage_extremes": extremes,
               "num_beats": beats_num,
               "mean_hr_bpm": mean_HR,
               "beats": time_beats}
    return metrics


def output_filename(filename):
    """Creates a name for output json file

    The function receives the name of the csv file that is being
    analyzed and creates the name of the output file using this
    inputted filename.

    Args:
        filename (string): name of csv file being analyzed

    Returns:
        string: name for the output json file
    """
    out_filename = "{}.json".format(filename)
    return out_filename


def output_json(filename, dict):
    """Outputs the dictionary of ecg signal information into
        a json file

    The function receives the name of the output file and the
    dictionary of ecg signal information and outputs the
    dictionary to a json using the output file name. This
    happens by opening the output file, dumping the metrics
    dictionary into the json file, and then closing the file.

    Args:
        filename (string): name of the output file
        dict (dictionary): dictionary of the ecg signal information

    Returns:
        json file: a json file with the dictionary inside
    """
    out_file = open(filename, 'w')
    json.dump(dict, out_file)
    out_file.close()


def ecg_driver(filename):
    """The main function of the script that runs all the functions

    This function is the main function of the code. It runs all
    of the functions created above in the correct order to get
    the desired output of a json file.

    Returns:
        json file: json file with a dictionary of ecg signal information
    """
    in_lines = read_file(filename)
    data = format_data(in_lines)
    s_data = separate_values(data)
    clean_data = remove_bad_data(s_data)
    time, volt = time_volt_lists(clean_data)
    filtered = BandPassFilter(volt)

    duration = duration_calc(time)
    time_beats = peak_find(time, filtered)
    beat_num = num_beats(time_beats)
    mean_HR = avg_HR(beat_num, duration)
    return time, filtered, round(mean_HR)


if __name__ == "__main__":
    ecg_driver()
