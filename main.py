from flask import Flask, render_template, Response, redirect, url_for, request
import cv2
from pyzbar.pyzbar import decode
import base64
import json, datetime
import qrcode
from io import BytesIO


app = Flask(__name__)
data = {
    'medicalhistory': {},
    'user': {}
}

decoded_data = None
qr_detected = False

@app.route("/qrscanned",methods=["GET", "POST"])
def qr_scanned():
    global decoded_data

    with open("data.txt", "r") as file:
        decoded_data = file.read()

    return decoded_data


@app.route("/patientdetails", methods=["GET", "POST"])
def patientdetails():
    global data

    if request.method == "GET":
        decoded_data = request.args.get("userInfo")

        if decoded_data:
            decoded_bytes = base64.b64decode(decoded_data)
            decoded_json = decoded_bytes.decode('utf-8')
            data = json.loads(decoded_json)
            if 'medicalhistory' not in data:
                data['medicalhistory'] = {}
            if 'user' not in data:
                data['user'] = {}
    if request.method == "POST" and "newpat" in request.form:
        with open("data.txt", "w") as file:
            file.write("")
        return redirect("/")

    if request.method == "POST" and "submitpres" in request.form:
        hospital_name = request.form.get("hospital_name")
        case = request.form.get("case")
        medication_name = request.form.get("medication_name")
        dosage = request.form.get("dosage")
        prescription_notes = request.form.get("prescription_notes")
        cTime = datetime.datetime.now().timestamp()

        if hospital_name not in data['medicalhistory']:
            data['medicalhistory'][hospital_name] = {}

        data['medicalhistory'][hospital_name][str(cTime)] = {
            "case": case,
            "medication_name": medication_name,
            "dosage": dosage,
            "prescription_notes": prescription_notes
        }
        json_string = json.dumps(data)
        encoded_data = base64.b64encode(json_string.encode('utf-8')).decode('utf-8')
        with open("data.txt", "w") as file:
            file.write(encoded_data)

    encoded_data = ""
    with open("data.txt","r") as file:
        encoded_data = file.read()

    return render_template("qrscanned.html", data=data, qrCode=encoded_data)

def gen():
    global qr_detected
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        global decoded_data
        decoded_objects = decode(frame)

        for obj in decoded_objects:
            decoded_data = obj.data.decode('utf-8')
            data = obj.data.decode('utf-8')
            cv2.putText(frame, data, (obj.rect.left, obj.rect.top), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            with open("data.txt", "w") as file:
                file.write(data)
            break
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True)
