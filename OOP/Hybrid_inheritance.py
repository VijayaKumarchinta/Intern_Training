class Grandfather:
    Grandfathername = "Oldman"
    def grandfather(self):
        print(f"Grandfather name is: {self.Grandfathername}")
class Grandmother:
    Grandmothername = "Oldlady"
    def grandmother(self):
        print(f"Grandmother name is: {self.Grandmothername}")
class Father(Grandfather,Grandmother):
    Fathername = "Gentleman"
    def father(self):
        print(f"Father name is: {self.Fathername}")
class Son(Father):
    Sonname = "Vijay"
    def Tree(self):
        print(f"Grandfather name: {self.Grandfathername}")
        print(f"Grandmother name: {self.Grandmothername}")
        print(f"Father name: {self.Fathername}")
        print(f"Son name: {self.Sonname}")
obj = Son()
try:
    obj.grandfather()
    obj.grandmother()
    obj.father()
    obj.Tree()
except AttributeError as e:
    print("Error:", e)