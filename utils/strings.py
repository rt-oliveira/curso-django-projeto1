def is_positive_number(string):
    try:
        number_string = float(string)
    except ValueError:
        return False

    return number_string > 0
