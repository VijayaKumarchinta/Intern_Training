nf = "note.txt"
try:
    with open(nf,"w") as cf:
        cf.write("This is a new file")
except FileNotFoundError:
    print("the file doesn't exist, first create a file")

try:
    with open(nf,"x") as cf:
        print("file created")
except FileExistsError:
    print("file already exist, create another one")

try:
    with open(nf,"a") as cf:
        cf.write("\nThis is a new line which is added earlier")
except Exception as e:
    print(f"the file error occured {e}")

try:
    with open(nf,"r+") as cf:
        print(cf.read())
except Exception as e:
    print(f"The file is not find {e}")
