import cv2
from cv2 import ROTATE_90_CLOCKWISE
import os
from flask import Flask, redirect, render_template, request, flash, url_for
from werkzeug.utils import secure_filename
from flask_wtf import FlaskForm
from wtforms import HiddenField, IntegerField, SubmitField
from flask_sqlalchemy import SQLAlchemy

class configClass():
    # DB settings
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database.db'   #File-based SQL DB
    SQLALCHEMY_TRACK_MODIFICATIONS = False              #Avoid SQLAlchemy warning
    UPLOAD_FOLDER = 'static/uploads/'
    MAX_CONTENT_LENGTH = 16*1024*1024
    SECRET_KEY = 'secret'

def createApp():
    # Get image through flask
    app = Flask(__name__)
    app.config.from_object(__name__ + '.configClass')
    db = SQLAlchemy(app)
    
    ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    @app.route('/')
    def upload_form():
        return render_template('upload.html')

    @app.route('/', methods=['POST'])
    def upload_image():
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No image detected for upload')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('Image uploaded')            
            # After upload, check content (oem) and send to addrem page
            img = cv2.imread(app.config['UPLOAD_FOLDER'] + filename, cv2.IMREAD_UNCHANGED)
            width = 800
            height = 800
            dim = (width, height)
            res_img = cv2.resize(img, dim, interpolation=cv2.INTER_AREA)
            detector = cv2.QRCodeDetector()
            rot_img = cv2.rotate(res_img,rotateCode=ROTATE_90_CLOCKWISE)
            data, bbox, straight_qrcode = detector.detectAndDecode(rot_img)
            if bbox is not None:
                print('Decoded data: ' + data)
                return redirect(url_for('addrem', data=data))  
            else:
                return 'nee'
        else:
            flash('Allowed image types -> png, jpg, jpeg, gif')
            return redirect(request.url)

    class AddRemForm(FlaskForm):
        oem = HiddenField('')
        amount = IntegerField('')
        addsubmit = SubmitField('Add')
        remsubmit = SubmitField('Remove')

    class Items(db.Model):
        __tablename__ = 'item_table'
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100, collation='NOCASE'), nullable=False)
        oem = db.Column(db.String(100, collation='NOCASE'), nullable=False)
        amount = db.Column(db.Integer, nullable=False)
        minamount = db.Column(db.Integer, nullable=False)

    @app.route('/addrem/<data>', methods=['POST', 'GET'])
    def addrem(data):
        addremform = AddRemForm()
        item = db.session.query(Items).filter(Items.oem==data).first()
        if addremform.addsubmit.data and addremform.validate_on_submit():
            item.amount = item.amount + addremform.amount.data
            db.session.commit()
            flash('Added ' + str(addremform.amount.data) + ' to item')
        if addremform.remsubmit.data and addremform.validate_on_submit():
            item.amount = item.amount - addremform.amount.data
            db.session.commit()
            flash('Removed ' + str(addremform.amount.data) + ' from item')
        return render_template('addrempage.html', data=data, amount=item.amount, addremform=addremform)

    return app

if __name__ == '__main__':
    app = createApp()
    app.run(host='0.0.0.0', port=8080, debug=True)