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
from skimage import data

np.random.seed(7)

height = 184 #~375/2
width = 616 #~1242/2
data_shape = height*width
classes = 2

# load the model:
with open('segNet_kitti_model.json') as model_file:
    segnet_basic = models.model_from_json(model_file.read())

# load weights
segnet_basic.load_weights("kitti_weights.best.hdf5")

# Compile model (required to make predictions)
segnet_basic.compile(loss="categorical_crossentropy", optimizer='adadelta', metrics=["accuracy"])

#load test data
test_data = np.load('./data/Kitti/test_data.npy')

batch_size = 1

# estimate accuracy on whole dataset using loaded weights
label_colours = np.array([[255, 0, 255], [0, 0, 0]])

#export data
data_path = './export/Kitti/'
images_path = './datasets/Kitti/test/'

images = glob.glob(images_path + "*.jpg") + glob.glob(images_path + "*.png")
images.sort()

index = 0
for test_image, image_file in zip(test_data, images):

    #read original image
    original_image = cv2.imread(image_file)
    original_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)

    #predict
    output = segnet_basic.predict_proba(test_image[np.newaxis, :])
    pred_image = vis.visualize(np.argmax(output[0],axis=1).reshape((height,width)), label_colours, False)
    
    #expand predict to the size of the original image
    expanded_pred = cv2.resize(pred_image, dsize=(1242, 375, 3)[:2], interpolation=cv2.INTER_CUBIC)

    #mark lane
    for i in range(1, original_image.shape[0]):
        for j in range(1,original_image.shape[1]):
            if (expanded_pred[i, j, 0] > 0):
                original_image[i,j,0] = 0
                original_image[i,j,2] = 0

    #save data
    image_name = data_path + str(index) + '.png' 
    io.imsave(image_name, original_image)

print('Done')