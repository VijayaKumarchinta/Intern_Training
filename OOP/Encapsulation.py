class Smartphone:
    def __init__(self,name,model,Code,HiddenApp):
        self.name = name
        self.model = model
        self._Code = Code
        self._HiddenApp = HiddenApp
        self.__battery_health = "100%"

    def show_details(self):
        print(f"Name: {self.name}, Model: {self.model}, Code: {self._Code}, Hidden App: {self._HiddenApp}")

    def check_battery_health(self):
        print(f"Battery health of {self.name} is {self.__battery_health}")

    def __privatecodes(self):
        print(f"Code of {self.name} is {self._Code}")

phone = Smartphone("iPhone", "12 Pro", "1234", "SecretApp")
try:
    phone.show_details()
    phone.check_battery_health()
except AttributeError as e:
    print(f"Error: {e}")