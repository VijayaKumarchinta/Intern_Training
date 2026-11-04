class Father:
    Father_name = "Gentleman"
    def fun1(self):
        print(f"Father name is: {self.Father_name}")
class Son(Father):
    Son_name = "Vijay"
    def fun2(self):
        print(f"Son name is: {self.Son_name}")

obj=Son()
try:
    obj.fun1()
    obj.fun2()
except AttributeError as e:
    print("Error:", e)