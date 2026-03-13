import abc

# -----------------------------------------#
# Abstract Base Classes                    #
# These classes have been hooked up to the #
# user interface as listeners.             #
# -----------------------------------------#

class CarparkSensorListener(abc.ABC):
    '''
    Your carpark management class should "implement" this abstract type (that is, 
    make a new class that inherits from this one, just like this class inherits
    from abc.ABC). When you hit the car in/out buttons or change the temperature,
    Your code should respond accordingly. See an example below! 
    '''
    @abc.abstractmethod
    def incoming_car(self,license_plate):
        '''Signals that a car has parked in an available bay'''
        pass
    @abc.abstractmethod
    def outgoing_car(self,license_plate):
        '''Signals that a car has left an occupied bay'''
        pass
    @abc.abstractmethod
    def temperature_reading(self,reading):
        '''Signals that a new temperature reading is available'''
        pass

class CarparkDataProvider(abc.ABC):
    '''
    This abstract class provides the display with its data.
    You should implement this class and provide your app's data
    through the properties here.

    Important! note about properties: they are methods but you use them like
    attributes. For example, if I make "x" a new CarparkDataProvider(),
    I can see the available spaces by referencing x.available_spaces.
    You might usually expect x.available_spaces() to be the way you'd
    access the data, but that won't work!
    '''
    @property
    @abc.abstractmethod
    def available_spaces(self):
        pass
    @property
    @abc.abstractmethod
    def temperature(self):
        pass
    @property
    @abc.abstractmethod
    def current_time(self):
        pass

