import csv

class CSVManager:

    def __init__(self):
        dfn = 'F:\Intern_Training\dataaaa.csv'
        self.dfn = dfn
    
    def write_csv(self, dt=None):

        try:
            fld = list(dt[0].keys())
            with open(self.dfn, 'w', newline='') as wcf:
                wt = csv.DictWriter(wcf, fieldnames=fld)
                wt.writeheader()
                wt.writerows(dt)
                print(f"Written {len(dt)} rows")
                return True
            
        except Exception as e:
            print(f"Error: {e}")
            return False
    def read_csv(self):

        try:
            with open(self.dfn,'r') as rf:
                rd = csv.DictReader(rf)
                dt = list(rd)
                return dt
            
        except FileNotFoundError:
            print("File not found")
            return []
    def append_csv(self,dt):

        try:
            with open(self.dfn,'r') as rf:
                rd = csv.DictReader(rf)
                fld = rd.fieldnames
            with open(self.dfn,'a',newline='') as af:
                wd = csv.DictWriter(af,fieldnames=fld)
                wd.writerows(dt)
            print(f"{len(dt)} Appended succesfully")
            return True
        
        except FileNotFoundError:
            print("File not found, use the write first")
            return False
    def count_rows(self):

        try:
            with open(self.dfn,'r') as crf:
                rd = csv.DictReader(crf)
                t=len(list(rd))
            print(f"Total rows: {t}")
            return t

        except Exception as e:
            print(f"Error occured while counting {e}")
if __name__ == "__main__":
    csv_mgr = CSVManager()

    employees = [
        {'name': 'John', 'age': 25, 'city': 'New York'},
        {'name': 'Jane', 'age': 30, 'city': 'London'},
        {'name': 'John cena', 'age':40, 'city': 'LA'}
    ]

    csv_mgr.write_csv(dt=employees)

    csv_mgr.read_csv()

    csv_mgr.append_csv([{'name': 'Alice', 'age': '28', 'city': 'Tokyo'}])
    
    csv_mgr.count_rows()