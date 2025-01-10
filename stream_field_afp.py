""" A printstream record field. """


class StreamFieldAFP:
    """ Attributes of a printstream record field. """
    
    def __init__(self, name=None, offset=None, length=None, type=None, optional=None, exception=None, range_min=None, range_max=None, range_values=None, meaning=None, value=None):
        self.name = name
        self.offset = offset
        self.length = length
        self.max_length = length
        self.type = type
        self.optional = optional
        self.exception = exception
        self.range_min = range_min
        self.range_max = range_max
        self.range_values = range_values  # List
        self.meaning = meaning  # List
        self.value = value
