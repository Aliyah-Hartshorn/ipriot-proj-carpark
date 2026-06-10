import threading
import time
import tkinter as tk 
from typing import Iterable 


from interfaces import CarparkSensorListener 
from interfaces import CarparkDataProvider 

# -------------------------------------------------
# Car Class
# ------------------------------------------------- 
class Car: 
    """
    Represents a car in the carpark. 
    Stores license plate and entry/exit times
    """
    
    def __init__(self, plate: str):
        self.license_plate = plate
        self.entry_time = time.localtime()
        self.exit_time = None

    def leave(self):
        """Record when the car leaves."""
        self.exit_time = time.localtime()


# -------------------------------------------------
# Carpark Manager
# -------------------------------------------------
class CarparkManager(CarparkSensorListener, CarparkDataProvider):
    """
    Core controller for the carpark system.
    """

    TOTAL_SPACES = 350

    def __init__(self):

        self.total_spaces = CarparkManager.TOTAL_SPACES
        self._available_spaces = self.total_spaces
        self._temperature = 0

        self.cars = {} 

        self.log_file = open("carpark_test.txt", "a")
    # -----------------------------
    # Data Provider Properties
    # -----------------------------
    @property
    def available_spaces(self):
        return self._available_spaces

    @property
    def temperature(self):
        return self._temperature

    @property
    def current_time(self):
        return time.localtime()

    # -----------------------------
    # Sensor Event Handlers
    # -----------------------------
    def incoming_car(self, license_plate):

        if not license_plate:
            return

        if license_plate in self.cars:
            return

        if self._available_spaces <= 0:
            self.log("Entry denied - full", license_plate)
            return

        car = Car(license_plate)
        self.cars[license_plate] = car

        self._available_spaces -= 1

        self.log("Car entered", license_plate)

    def outgoing_car(self, license_plate):

        if license_plate not in self.cars:
            self.log("Unknown car exit", license_plate)
            return

        car = self.cars.pop(license_plate)
        car.leave()

        self._available_spaces = min(self._available_spaces + 1, self.total_spaces)

        self.log("Car exited", license_plate)

    def temperature_reading(self, reading):

        self._temperature = reading
        self.log("Temperature update", reading)

    def __del__(self):
        if hasattr(self, 'log_file') and not self.log_file.closed:
            self.log_file.close()

    # -----------------------------
    # Logging
    # -----------------------------
    def log(self, event, value):

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.log_file.write(f"{timestamp} | {event} | {value}\n")
        self.log_file.flush()


# -------------------------------------------------
# GUI Display
# -------------------------------------------------
class WindowedDisplay:

    DISPLAY_INIT = '---'
    SEP = ':'

    def __init__(self, root, title: str, display_fields: Iterable[str]):

        self.window = tk.Toplevel(root)
        self.window.title(f'{title}: Parking')
        self.window.geometry('800x400')
        self.window.resizable(False, False)

        self.display_fields = display_fields
        self.gui_elements = {}

        for i, field in enumerate(display_fields):

            self.gui_elements[f'lbl_field_{i}'] = tk.Label(
                self.window, text=field+self.SEP, font=('Arial', 50))

            self.gui_elements[f'lbl_value_{i}'] = tk.Label(
                self.window, text=self.DISPLAY_INIT, font=('Arial', 50))

            self.gui_elements[f'lbl_field_{i}'].grid(
                row=i, column=0, sticky=tk.E, padx=5, pady=5)

            self.gui_elements[f'lbl_value_{i}'].grid(
                row=i, column=2, sticky=tk.W, padx=10)

    def show(self):
        pass

    def update(self, updated_values: dict):

        for field in self.gui_elements:
            if field.startswith('lbl_field'):
                field_value = field.replace('field', 'value')

                name = self.gui_elements[field].cget('text').rstrip(self.SEP)

                self.gui_elements[field_value].configure(
                    text=updated_values[name]
                )

        self.window.update()


# -------------------------------------------------
# Carpark Display
# -------------------------------------------------
class CarParkDisplay:

    fields = ['Available bays', 'Temperature', 'At']

    def __init__(self, root):

        self.window = WindowedDisplay(root, 'Moondalup', CarParkDisplay.fields)

        self._provider = None

        updater = threading.Thread(target=self.check_updates)
        updater.daemon = True
        updater.start()

        self.window.show()

    @property
    def data_provider(self):
        return self._provider

    @data_provider.setter
    def data_provider(self, provider):
        if isinstance(provider, CarparkDataProvider):
            self._provider = provider

    def update_display(self):

        field_values = dict(zip(CarParkDisplay.fields, [

            f'{self._provider.available_spaces:03d}',
            f'{int(self._provider.temperature):02d}°C' ,
            time.strftime("%H:%M:%S", self._provider.current_time)

        ]))

        self.window.update(field_values)

    def check_updates(self):

        while True:

            time.sleep(1)

            if self._provider is not None:
                self.update_display()


# -------------------------------------------------
# Car Detector Window
# -------------------------------------------------
class CarDetectorWindow:

    def __init__(self, root):

        self.root = root
        self.root.title("Car Detector")

        self.listeners = []

        self.btn_incoming = tk.Button(
            root,
            text="Incoming Car",
            font=('Arial', 40),
            command=self.incoming_car
        )
        self.btn_incoming.grid(row=0, column=0, columnspan=2, pady=10)

        self.btn_outgoing = tk.Button(
            root,
            text="Outgoing Car",
            font=('Arial', 40),
            command=self.outgoing_car
        )
        self.btn_outgoing.grid(row=1, column=0, columnspan=2, pady=10)

        tk.Label(root, text="Temperature", font=('Arial', 20)).grid(row=2, column=0)

        self.temp_var = tk.StringVar()
        self.temp_var.trace_add(
            "write",
            lambda *args: self._on_temp_changed()
        )

        tk.Entry(root, textvariable=self.temp_var, font=('Arial', 20)).grid(row=2, column=1)

        tk.Label(root, text="License Plate", font=('Arial', 20)).grid(row=3, column=0)

        self.plate_var = tk.StringVar()

        tk.Entry(root, textvariable=self.plate_var, font=('Arial', 20)).grid(row=3, column=1)

    @property
    def current_license(self):
        return self.plate_var.get()

    def _on_temp_changed(self):
        try:
            value = float(self.temp_var.get())
            for listener in self.listeners:
                listener.temperature_reading(value)
        except ValueError:
            pass  # Ignore incomplete or invalid input

    def add_listener(self, listener):
        if isinstance(listener, CarparkSensorListener):
            self.listeners.append(listener)

    def incoming_car(self):

        for listener in self.listeners:
            listener.incoming_car(self.current_license)

    def outgoing_car(self):

        for listener in self.listeners:
            listener.outgoing_car(self.current_license)

    def temperature_changed(self, temp):
        # Kept for external callers; internal use goes via _on_temp_changed
        for listener in self.listeners:
            listener.temperature_reading(temp)


# -------------------------------------------------
# Main Program
# -------------------------------------------------
if __name__ == "__main__":

    root = tk.Tk()

    manager = CarparkManager()

    display = CarParkDisplay(root)
    display.data_provider = manager

    detector = CarDetectorWindow(root)
    detector.add_listener(manager)

    root.mainloop()