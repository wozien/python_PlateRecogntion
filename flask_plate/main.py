# -*- coding: utf-8 -*-
import os
import uuid
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
from flask import send_from_directory
# from flask_plate.db import get_db

import time
import cv2
import numpy
from .lib import img_function as predict
from .lib import img_math as img_math
from PIL import Image, ImageTk, ImageGrab


predictor = predict.CardPredictor()
predictor.train_svm()

bp = Blueprint('main', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
IMAGE_FOLDER = bp.root_path + '/../images/'
TMP_FOLDER = bp.root_path + '/tmp/'

try:
    os.makedirs(IMAGE_FOLDER)
except OSError:
    pass

try:
    os.makedirs(TMP_FOLDER)
except OSError:
    pass


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        if 'car_image' not in request.files:
            flash('No car image')
            return redirect(request.url)
        image = request.files['car_image']
        if image.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if not image or not allowed_file(image.filename):
            flash('No selected file')
            return redirect(request.url)
        image_uuid = uuid.uuid4().hex
        filename = ''.join([image_uuid, '.', image.filename.rsplit('.', 1)[1]])
        image.save(os.path.join(IMAGE_FOLDER, filename))
        image_path = os.path.join(IMAGE_FOLDER, filename)
        result = {}
        try:
            result = pic(image_path)
            result.update({
                'result': '识别成功'
            })
        except Exception as e:
            flash(e)
            result.update({
                'result': '识别失败'
            })
        return render_template('index.html', filepath='/image/'+filename, result=result)
    return render_template('index.html')


@bp.route('/image/<filename>')
def show_img(filename):
    return send_from_directory(IMAGE_FOLDER, filename)


@bp.route('/tmp/<filename>')
def show_tmp_img(filename):
    return send_from_directory(TMP_FOLDER, filename)


def pic(pic_path):
    img_bgr = img_math.img_read(pic_path)
    first_img, oldimg = predictor.img_first_pre(img_bgr)
    r_c, roi_c, color_c = predictor.img_color_contours(first_img, oldimg)
    r_color, roi_color, color_color = predictor.img_only_color(oldimg, oldimg, first_img)
    if not color_color:
        color_color = color_c
    if not color_c:
        color_c = color_color
    roi_c = cv2.cv2.cvtColor(roi_c, cv2.cv2.COLOR_BGR2RGB)
    roi_color = cv2.cv2.cvtColor(roi_color, cv2.cv2.COLOR_BGR2RGB)
    cv2.cv2.imwrite(TMP_FOLDER+"img_color_contours.png", roi_c)
    cv2.cv2.imwrite(TMP_FOLDER+"img_only_color.png", roi_color)
    print(color_c, r_c, "|", color_color, r_color)
    return {
        'img_color_contours': '颜色形状识别结果: ' + color_c + ' ' + r_c,
        'img_color_contours_path': '/tmp/img_color_contours.png',
        'img_only_color': '颜色识别结果: ' + color_c + ' ' + r_c,
        'img_only_color_path': '/tmp/img_only_color.png',
    }
