from email.mime import image
from queue import Empty
import numpy as np
import pyodbc
import json
import base64
from flask import jsonify
from datetime import datetime

import os
from azure.storage.blob import BlobServiceClient
import cv2
import ast
import PIL.Image as Image
import io
import mediapipe as mp

server = 'Add server'
database = 'database name'
username = 'Add username'
password = '*******'
driver= '{ODBC Driver 17 for SQL Server}'

def add_data_to_attendence(course_id, course_name,professor_name, longi, lati):
    status = 0
    date = datetime.now()
    date = date.strftime("%d/%m/%Y")
    conn = pyodbc.connect('DRIVER='+driver+';PORT=1433;SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    cursor = conn.cursor()
    cursor.execute('INSERT INTO [dbo].[attendence] (course_id, course_name, professor_name, date,longi, lati) VALUES (?,?,?,?,?,?)',course_id, course_name, professor_name, date,longi, lati)
    status = 1
    return {'status_code' : status}

def select_professor_from_course(professor_id,term):
    conn = conn = pyodbc.connect('DRIVER='+driver+';PORT=1433;SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+ password)
    cursor = conn.cursor()
    if professor_id and not term:
        cursor.execute('SELECT * FROM [dbo].[prof_course] WHERE prof_id=?',professor_id)
        row_data = cursor.fetchall()
        row_data = [row for row in row_data]
        column_names = [column.column_name for column in cursor.columns(table='prof_course')]
        data = [dict(zip(column_names,data)) for data in row_data]

        course_name = [i.get('registered_course') for i in data]
        course_column_name = [column.column_name for column in cursor.columns(table='subject')]
        
        final_course_data = []
        # subject table
        for name in course_name:
            cursor.execute('SELECT * FROM [dbo].[subject] WHERE course_name=?',name)
            course_data = cursor.fetchall()
            course_row_data = [row for row in course_data]
            
            # print('column_name=>', course_column_name)
            final_course_data.append([dict(zip(course_column_name,data)) for data in course_row_data])

        dict_data = []

        for i in range(len(data)):
            dict_data.append(dict(data[i], **final_course_data[i][0]))

    elif term and not professor_id:
        cursor.execute('SELECT * FROM [dbo].[prof_course] WHERE term=?',term)
        rows = cursor.fetchall()
        row_data = []
        for row in rows:
            temp = []
            for i in row:
                temp.append(str(i).strip())
            row_data.append(temp)
        column_names = [i.column_name for i in cursor.columns(table='prof_course')]

        data = [dict(zip(column_names,data)) for data in row_data]

        course_name = [i.get('registered_course') for i in data]
        
        final_course_data = []
        course_column_name = [column.column_name for column in cursor.columns(table='subject')]
        # subject table
        for name in course_name:
            cursor.execute('SELECT * FROM [dbo].[subject] WHERE course_name=?',name)
            course_data = cursor.fetchall()
            course_row_data = [row for row in course_data]
            
            final_course_data.append([dict(zip(course_column_name,data)) for data in course_row_data])

        dict_data = []

        for i in range(len(data)):
            # new_dic = data[i].copy()
            dict_data.append(dict(data[i], **final_course_data[i][0]))

    elif professor_id and term:
        cursor.execute('SELECT * FROM [dbo].[prof_course] WHERE  prof_id=? AND term=?', professor_id, term)
        row_data = cursor.fetchall()
        row_data = [row for row in row_data]
        column_names = [column.column_name for column in cursor.columns(table='prof_course')]
        data = [dict(zip(column_names,data)) for data in row_data]

        course_name = [i.get('registered_course') for i in data]
        
        final_course_data = []
        course_column_name = [column.column_name for column in cursor.columns(table='subject')]
        # subject table
        for name in course_name:
            cursor.execute('SELECT * FROM [dbo].[subject] WHERE course_name=?',name)
            course_data = cursor.fetchall()
            course_row_data = [row for row in course_data]
            
            # print('column_name=>', course_column_name)
            final_course_data.append([dict(zip(course_column_name,data)) for data in course_row_data])

        dict_data = []

        for i in range(len(data)):
            # new_dic = data[i].copy()
            dict_data.append(dict(data[i], **final_course_data[i][0]))
            # print(final_course_data[i][0])
            # print(data[i])
        
    return {'data': dict_data}


def examine_student_while_exam(img,img_name, exam_id, student_id, time):
    status = 0

    # print('started!')
    conn_str = "****************"
    
    blob_service_client = BlobServiceClient.from_connection_string(conn_str)
    
    container_client = blob_service_client.get_container_client(student_id)

    files = blob_service_client.list_containers()

    file_names = []
    for file in files:
        file_names.append(str(file.name))
    

    imgdata = base64.b64decode(str(img))
    
    image = np.array(Image.open(io.BytesIO(imgdata)))
    image = cv2.resize(image,(512,512))
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    is_success, im_buf_arr = cv2.imencode('.jpeg',np.array(image))
    bytes_im = im_buf_arr.tobytes()
    
    if student_id in file_names:
 
        date = datetime.now()
        new_blob_name = img_name 
        
        container_client.upload_blob(name=new_blob_name+".jpg",data=bytes_im)

    else:
        
        blob_service_client.create_container(str(student_id), public_access='container')
        
        date = datetime.now()
        new_blob_name = img_name

        container_client.upload_blob(name=new_blob_name+".jpg",data=bytes_im)

    container_client_student_id = blob_service_client.get_container_client(student_id)
    blob_url = "https://studentcheckforexam.blob.core.windows.net/"+ str(student_id) + "/" + str(new_blob_name)+".jpg"

    blob_client = blob_service_client.get_blob_client(container=student_id, blob=new_blob_name+'.png')
    
   
    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    gray_img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            
    img_width = img.shape[1]
    img_height = img.shape[0]

    mp_face_detection = mp.solutions.face_detection

    with mp_face_detection.FaceDetection(min_detection_confidence=0.5) as face_detection:
        image = cv2.cvtColor(image ,cv2.COLOR_BGR2RGB)
        image = cv2.resize(image ,(512,512))
        gray_img = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        img_width = image.shape[1]
        img_height = image.shape[0]
        results = face_detection.process(image)

        if results.detections:
            for detection in results.detections:
                bounding_box = detection.location_data.relative_bounding_box
                landmarks = detection.location_data.relative_keypoints
                x = int(bounding_box.xmin * img_width)
                w = int(bounding_box.width * img_width)
                y = int(bounding_box.ymin * img_height)
                h = int(bounding_box.height * img_height)

                if x>0 and y>0:
                    detected_face = image[y:y+h, x:x+w]
                    test_img = cv2.resize(gray_img[y:y+h, x:x+w], (512,512))
            
            conn_str_yml = "*****"
            
            blob_service_client_yml = BlobServiceClient.from_connection_string(conn_str_yml)
            
            container_client_yml = blob_service_client_yml.get_container_client(student_id)
            files_yml = container_client_yml.list_blobs()

            for file in files_yml:
                
                if file.name == student_id:
                    blob_client_yml = blob_service_client_yml.get_blob_client(container=student_id, blob=student_id)
                    
                    blob_read = blob_client_yml.download_blob()
                    with open(student_id+'.yml', 'wb') as download_file:
                        download_file.write(blob_read.readall())
                            
                    reco = cv2.face.LBPHFaceRecognizer_create()
                    reco.read(student_id+'.yml')
                    # predicting new image
                    Id, coef = reco.predict(gray_img)
                    print('coef=>',coef)
                    
                    if coef > 100:
                        match = 'true'
                    else:
                        match = 'false'
                    
                    download_file.close()
                    os.remove(student_id+'.yml')
        else:
            match = 'true'
    
    conn = pyodbc.connect('DRIVER='+driver+';PORT=1433;SERVER='+server+';PORT=1443;DATABASE='+database+';UID='+username+';PWD='+ password)
    cursor = conn.cursor()


    names = cursor.execute('SELECT total_marks FROM [dbo].[exam] WHERE exam_id=?', exam_id)
    total_marks_row = names.fetchall()
    update_dict = ast.literal_eval(total_marks_row[0][0])

    if student_id in update_dict.keys():
        
        old_val = update_dict[student_id]
        

        if 'log' in old_val[0].keys():
            past_val = old_val[0]['log']

            new_dict = {}
            new_dict['time'] = time
            new_dict['is_cheating'] = str(match)
            new_dict['url'] = blob_url
            past_val.append(new_dict)

            old_val[0]['log'] = past_val

            data = {}
            data[student_id] = old_val

            final_data = {**update_dict, **data}

        else:

            new_dict = {}
            new_dict['time'] = time
            new_dict['is_cheating'] = str(match)
            new_dict['url'] = blob_url
            
            old_val[0]['log'] = [new_dict]

            data = {}
            data[student_id] = old_val

            final_data = {**update_dict, **data}

        cursor.execute("UPDATE [dbo].[exam] SET total_marks=? WHERE exam_id=?", json.dumps(final_data), exam_id)
        cursor.commit()
        cursor.close()
    else:
        new_data = dict()
        new_data['time'] = time
        new_data['is_cheating'] = str(match)
        new_data['url'] = blob_url

        data = dict()
        data['log'] = [new_data]

        final_dict = dict()
        final_dict[student_id] = [data]

        final_data = {**update_dict, **final_dict}

        cursor.execute("UPDATE [dbo].[exam] SET total_marks=? WHERE exam_id=?", json.dumps(final_data), exam_id)
        cursor.commit()
        cursor.close()

    status = 1
    return {'status': status}
