""" Base afp class """


class AFPClass:

    def __str__(self):
        """ Iterate over all attributes, and create the representative string. """
        return ", ".join([f"{key}:{value}" for key, value in self.__dict__.items()])
