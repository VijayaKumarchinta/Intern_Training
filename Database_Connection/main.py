from flask import Flask, jsonify, request
from flask.views import MethodView
from setup import Postgremanager

app = Flask(__name__)
db = Postgremanager()

class EmpView(MethodView):

    def get(self, email=None):
        try:
            if email:
                all_emps = db.fetch_all_employees()
                for emp in all_emps:
                    if emp["email"] == email:
                        return jsonify({"status": "success", "data": emp}), 200
                return jsonify({"status": "error", "message": f"Employee '{email}' not found"}), 404

            emps = db.fetch_all_employees()
            return jsonify({"status": "success", "count": len(emps), "data": emps}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    def post(self):
        try:
            d = request.get_json()
            if not d:
                return jsonify({"status": "error", "message": "No JSON data provided"}), 400

            items = []
            if type(d) == list:
                for emp in d:
                    items.append(emp)
            else:
                items.append(d)
                
            required = ["first_name", "last_name", "email", "phone", "hire_date"]
            i = 0
            for emp in items:
                i += 1
                missing = []
                for fie in required:
                    if fie not in emp:
                        missing.append(fie)
                if missing:
                    return jsonify({"status": "error", "message": f"Employee {i}: missing {', '.join(missing)}"}), 400

            count = db.insert_employee(items)
            if count > 0:
                msg = f"{count} employee added" if count == 1 else f"{count} employees added"
                return jsonify({"status": "success", "message": msg}), 201
            return jsonify({"status": "error", "message": "Failed to add employee(s)"}), 500
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    def put(self, email):
        try:
            d = request.get_json()
            if not d:
                return jsonify({"status": "error", "message": "No JSON data provided"}), 400

            upd = db.update_employee(email, d)
            if upd:
                return jsonify({"status": "success", "message": f"Employee '{email}' updated"}), 200
            return jsonify({"status": "error", "message": f"Employee '{email}' not found"}), 404
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    def delete(self, email):
        try:
            del_ = db.delete_employee(email)
            if del_:
                return jsonify({"status": "success", "message": f"Employee '{email}' deleted"}), 200
            return jsonify({"status": "error", "message": f"Employee '{email}' not found"}), 404
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

app.add_url_rule("/employees", view_func=EmpView.as_view("employees"))
app.add_url_rule("/employees/<email>", view_func=EmpView.as_view("employee_detail"))


if __name__ == "__main__":
    try:
        db.create_db()
        db.create_schema()
        db.create_table()
        print("Starting Employee API server...")
        app.run(debug=False)
    except Exception as e:
        print(f"Failed to start server: {e}")