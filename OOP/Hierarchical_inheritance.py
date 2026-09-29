class Father:
    Fathername = "Gentleman"
    def father(self):
        print(self.Fathername)
class Firstchild(Father):
    def firstchild(self):
        print(f"First child name is: {self.Fathername}")
class Secondchild(Father):
    def secondchild(self):
        print(f"Second child name is: {self.Fathername}")

f1 = Firstchild()
f2 = Secondchild()
try:
    f1.father()
    f1.firstchild()
    f2.secondchild()
    f2.father()
except AttributeError as e:
    print("Error:", e)