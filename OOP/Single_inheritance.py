class Father:
    Fathername = "Gentleman"
    def fun1(self):
        print(f"Father name is: {self.Fathername}")
class Son(Father):
    Sonname = "Vijay"
    def fun2(self):
        print(f"Son name is: {self.Sonname}")

obj=Son()
try:
    obj.fun1()
    obj.fun2()
except AttributeError as e:
    print("Error:", e)