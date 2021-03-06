#usage 
#python eval-kitti.py --net=segnet

#rename result files with commands below:
#rename 's/umm_/umm_road_/' 

from __future__ import absolute_import
from __future__ import print_function
import os

os.environ['KERAS_BACKEND'] = 'theano'
#os.environ['THEANO_FLAGS']='mode=FAST_RUN,device=cuda,floatX=float32,optimizer=None'

import keras.models as models
from keras.layers.core import Layer, Dense, Dropout, Activation, Flatten, Reshape, Permute
from keras.layers.convolutional import Convolution2D, MaxPooling2D, UpSampling2D, ZeroPadding2D
from keras.layers.normalization import BatchNormalization
from keras.callbacks import ModelCheckpoint

from keras import backend as K
K.set_image_data_format('channels_first')

import cv2
import numpy as np
import json
import visualize as vis
from skimage import io
import glob
from skimage import data, transform
import argparse
from helper import *

np.random.seed(7)

#parser
parser = argparse.ArgumentParser()
parser.add_argument("--net", type = str)
args = parser.parse_args()
net_parse = args.net
print(net_parse)

#shape
height = 184 #~375/2
width = 616 #~1242/2
data_shape = height*width
classes = 2

# define parameters
json_model, weights_file = "", ""
if net_parse == "unet":
    json_model = 'uNet_kitti_model.json'
    weights_file = "unet_kitti_weights.best.hdf5"
else:
    json_model = 'segNet_kitti_model.json'
    weights_file = "segnet_kitti_weights.best.hdf5"

# load the model:
with open(json_model) as model_file:
    net_basic = models.model_from_json(model_file.read())

# load weights
net_basic.load_weights(weights_file)

# Compile model (required to make predictions)
net_basic.compile(loss="categorical_crossentropy", optimizer='adadelta', metrics=["accuracy"])

batch_size = 1

# estimate accuracy on whole dataset using loaded weights
label_colours = np.array([[255, 0, 0],[255, 0, 255]])

#load test data
datasets = ['train'] #['test', 'train']

for dataset in datasets:

    #data = np.load('./data/Kitti/' + dataset + '_data.npy')

    #export data
    save_path = './export/Kitti/' + net_parse + '/' + dataset + '/'
    #images_path = './datasets/Kitti/' + dataset + '/'
    images_path = './datasets/data_road/falreis/' + dataset + '/'
    
    images_paths = glob.glob(images_path + "*.jpg") + glob.glob(images_path + "*.png")
    images_paths.sort()

    print(save_path)
    print(images_path)

    index = 0
    len_data = len(images_paths)
    #for test_image, image_path in zip(data, images_paths):
    for image_path in images_paths[285:]:

        #read original image
        original_image = cv2.imread(image_path)
        original_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
        original_width = original_image.shape[1]
        original_height = original_image.shape[0]

        reduced_image = cv2.resize(cv2.imread(image_path), dsize=(width, height, 3)[:2], interpolation=cv2.INTER_CUBIC)
        test_image = np.rollaxis(normalized(reduced_image), 2) 

        #predict
        #output = net_basic.predict_proba(test_image[np.newaxis, :])
        output = net_basic.predict(test_image[np.newaxis, :])
        pred_image = vis.visualize(np.argmax(output[0],axis=1).reshape((height,width)), label_colours, False)
        
        #expand predict to the size of the original image
        expanded_pred = transform.resize(pred_image, (original_height, original_width, 3)).astype(np.float)
        #expanded_pred = cv2.resize(pred_image, dsize=(original_width, original_height, 3)[:2], interpolation=cv2.INTER_CUBIC)

        #mark lane
        
        for i in range(1, original_height):
            for j in range(1, original_width):                
                if (expanded_pred[i, j, 2] > 0):
                    #expanded_pred[i,j,:] = [255, 255, 255]
                    original_image[i,j,0] = 0
                    original_image[i,j,2] = 0
        
        #save data
        pos = image_path.rfind('/')
        name_file = image_path[pos+1:]
        #io.imsave((save_path + name_file), expanded_pred)
        io.imsave((save_path + name_file), original_image)
        
        #verbose
        index += 1
        print(index, '/', len_data, end='')
        print('\r', end='')

print("Done")
#print("Just remember rename files to use KITTI eval tool.")
#print("Instructions in the beggining of the file - comment section!")
#print(">> rename 's/umm_/umm_road_/' * ")
#print(">> rename 's/um_/um_lane_/' * ")
#print(">> rename 's/uu_/uu_road_/' * ")