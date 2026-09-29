class Mother:
    Mothername = "Lady"
    motherage = 40
    def mother(self):
        print(self.Mothername)
        print(self.motherage)
class Father:
    Fathername = "Gentleman"
    fatherage = 47
    def father(self):
        print(self.Fathername)
        print(self.fatherage)
class Son(Mother,Father):
    def parents(self):
        print(f"Father name : {self.Fathername} and age is {self.fatherage}")
        print(f"Mother name : {self.Mothername} and age is {self.motherage}")

s1 = Son()
try:
    s1.father()
    s1.mother()
    s1.parents()
except AttributeError as e:
    print("Error:", e)
