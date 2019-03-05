#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 26 13:33:38 2019

@author: xu
"""

from flask import Flask,request,jsonify
import tensorflow as tf
from test import imageprepare,weight_variable,bias_variable,conv2d,max_pool_2x2
import os
from werkzeug.utils import secure_filename
from PIL import Image
import time 

import logging

from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement

global f

app = Flask(__name__)

log = logging.getLogger()
log.setLevel('INFO')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
log.addHandler(handler)

cluster = Cluster(contact_points=['cassandra'],port=9042)
session = cluster.connect()

KEYSPACE = "xukeyspace"

def createKeySpace():   
    log.info("Creating keyspace...")
    try:
        session.execute("""
            CREATE KEYSPACE IF NOT EXISTS %s
            WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '1' }
            """ % KEYSPACE)
        log.info('setting keyspace...')
        session.set_keyspace(KEYSPACE)
        log.info("creating table...")
        session.execute("""
           CREATE TABLE IF NOT EXISTS xutable (
               picture_name text,
               predict_number text,
               date text,
               PRIMARY KEY (date)
           )
           """)
    except Exception as e:
        log.error("Unable to create table")
        log.error(e)


def insertdata(final):
    global f
    try:
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        session.execute("""
                INSERT INTO xutable (picture_name, predict_number, date)
                VALUES ('%s', '%s', '%s')
                """ % (str(f.filename), final, now)
                )
        log.info("%s, %s, %s" % (str(f.filename), final, now))
        log.info("Data stored!")
    except Exception as e:
        log.error("Unable to insert data!")
        log.error(e)
    return final
    

ALLOWED_EXTENSIONS = set(["png", "jpg", "JPG", "PNG", "bmp"])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route("/upload",methods=["GET","POST"])
def upload():
    global f
    if request.method== "POST" :
        createKeySpace()
        f= request.files["file"]
        if not (f and allowed_file(f.filename)):
            return jsonify({"error": 1001, "msg": "请检查上传的图片类型，仅限于png、PNG、jpg、JPG、bmp"})
        basepath = os.path.dirname(__file__)  # 当前app.py文件所在路径
 
        upload_path = os.path.join(basepath, secure_filename(f.filename))  
        
        f.save(upload_path)
 
        img = Image.open(upload_path)
        result=imageprepare(img)
        x = tf.placeholder(tf.float32, [None, 784])

        y_ = tf.placeholder(tf.float32, [None, 10])
        W_conv1 = weight_variable([5, 5, 1, 32])
        b_conv1 = bias_variable([32])

        x_image = tf.reshape(x,[-1,28,28,1])

        h_conv1 = tf.nn.relu(conv2d(x_image,W_conv1) + b_conv1)
        h_pool1 = max_pool_2x2(h_conv1)

        W_conv2 = weight_variable([5, 5, 32, 64])
        b_conv2 = bias_variable([64])

        h_conv2 = tf.nn.relu(conv2d(h_pool1, W_conv2) + b_conv2)
        h_pool2 = max_pool_2x2(h_conv2)

        W_fc1 = weight_variable([7 * 7 * 64, 1024])
        b_fc1 = bias_variable([1024])

        h_pool2_flat = tf.reshape(h_pool2, [-1, 7*7*64])
        h_fc1 = tf.nn.relu(tf.matmul(h_pool2_flat, W_fc1) + b_fc1)

        keep_prob = tf.placeholder("float")
        h_fc1_drop = tf.nn.dropout(h_fc1, keep_prob)

        W_fc2 = weight_variable([1024, 10])
        b_fc2 = bias_variable([10])

        y_conv=tf.nn.softmax(tf.matmul(h_fc1_drop, W_fc2) + b_fc2)

        cross_entropy = -tf.reduce_sum(y_*tf.log(y_conv))
        train_step = tf.train.AdamOptimizer(1e-4).minimize(cross_entropy)
        correct_prediction = tf.equal(tf.argmax(y_conv,1), tf.argmax(y_,1))
        accuracy = tf.reduce_mean(tf.cast(correct_prediction, "float"))

        saver = tf.train.Saver()

        with tf.Session() as sess:
            sess.run(tf.global_variables_initializer())
            saver.restore(sess, '/root/mnist/model.ckpt') 

            prediction=tf.argmax(y_conv,1)
            predint=prediction.eval(feed_dict={x: [result],keep_prob: 1.0}, session=sess)

            print('result:')
            print(predint[0])
            final=str(predint[0])
            insertdata(final)
            return final
        
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
    app.debug=True
