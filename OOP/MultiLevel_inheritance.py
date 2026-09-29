class GrandFather:
    grandfather_name = "Wise man"
    grandfather_age = 70
    def grandfather(self):
        print(self.grandfather_name)
        print(self.grandfather_age)
class Father(GrandFather):
    Fathername = "Gentleman"
    Fatherage = 48
    def father(self):
        print(f"Father name is: {self.Fathername}")
        print(f"Father age is: {self.Fatherage}")
class Son(Father):
    Sonname = "Vijay"
    Sonage = 21
    def Tree(self):
        print(f"Father name : {self.Fathername} and age is {self.Fatherage}")
        print(f"Grandfather name : {self.grandfather_name} and age is {self.grandfather_age}")
        print(f"Son name : {self.Sonname} and age is {self.Sonage}")
obj = Son()
try:
    obj.grandfather()
    obj.father()
    obj.Tree()
except AttributeError as e:
    print("Error:", e)