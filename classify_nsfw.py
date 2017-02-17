#!/usr/bin/env python
"""
Copyright 2016 Yahoo Inc.
Licensed under the terms of the 2 clause BSD license. 
Please see LICENSE file in the project root for terms.
"""

import numpy as np
import os
import sys
import argparse
import glob
import time
from PIL import Image
from StringIO import StringIO
import caffe
from util import get_image
from bottle import route, request, response, template, run
import json
import time
from urllib2 import HTTPError, URLError

# Pre-load caffe model.
nsfw_net = caffe.Net('nsfw_model/deploy.prototxt', 'nsfw_model/resnet_50_1by2_nsfw.caffemodel', caffe.TEST)

# Load transformer
# Note that the parameters are hard-coded for best results
caffe_transformer = caffe.io.Transformer({'data': nsfw_net.blobs['data'].data.shape})
caffe_transformer.set_transpose('data', (2, 0, 1))  # move image channels to outermost
caffe_transformer.set_mean('data', np.array([104, 117, 123]))  # subtract the dataset-mean value in each channel
caffe_transformer.set_raw_scale('data', 255)  # rescale from [0, 1] to [0, 255]
caffe_transformer.set_channel_swap('data', (2, 1, 0))  # swap channels from RGB to BGR


def resize_image(data, sz=(256, 256)):
    """
    Resize image. Please use this resize logic for best results instead of the 
    caffe, since it was used to generate training dataset 
    :param str data:
        The image data
    :param sz tuple:
        The resized image dimensions
    :returns bytearray:
        A byte array with the resized image
    """
    img_data = str(data)
    im = Image.open(StringIO(img_data))
    if im.mode != "RGB":
        im = im.convert('RGB')
    imr = im.resize(sz, resample=Image.BILINEAR)
    fh_im = StringIO()
    imr.save(fh_im, format='JPEG')
    fh_im.seek(0)
    return bytearray(fh_im.read())

def caffe_preprocess_and_compute(pimg, caffe_transformer=None, caffe_net=None,
    output_layers=None):
    """
    Run a Caffe network on an input image after preprocessing it to prepare
    it for Caffe.
    :param PIL.Image pimg:
        PIL image to be input into Caffe.
    :param caffe.Net caffe_net:
        A Caffe network with which to process pimg afrer preprocessing.
    :param list output_layers:
        A list of the names of the layers from caffe_net whose outputs are to
        to be returned.  If this is None, the default outputs for the network
        are returned.
    :return:
        Returns the requested outputs from the Caffe net.
    """
    if caffe_net is not None:

        # Grab the default output names if none were requested specifically.
        if output_layers is None:
            output_layers = caffe_net.outputs

        img_data_rs = resize_image(pimg, sz=(256, 256))
        image = caffe.io.load_image(StringIO(img_data_rs))

        H, W, _ = image.shape
        _, _, h, w = caffe_net.blobs['data'].data.shape
        h_off = max((H - h) / 2, 0)
        w_off = max((W - w) / 2, 0)
        crop = image[h_off:h_off + h, w_off:w_off + w, :]
        transformed_image = caffe_transformer.preprocess('data', crop)
        transformed_image.shape = (1,) + transformed_image.shape

        input_name = caffe_net.inputs[0]
        all_outputs = caffe_net.forward_all(blobs=output_layers,
                    **{input_name: transformed_image})

        outputs = all_outputs[output_layers[0]][0].astype(float)
        return outputs
    else:
        return []

@route('/porn_image')
def porn_image():
    mode = request.query.mode
    url = request.query.url
    begin = time.time()
    filename = get_image(url)
    if filename == '00000.jpg':
        return 'Image is too large!'
    try:
        image_data = open(filename).read()
    except (HTTPError, URLError):
        return "Image can not be found!"

    after_download_image = time.time()
    # Classify.
    try:
        scores = caffe_preprocess_and_compute(image_data, caffe_transformer=caffe_transformer, caffe_net=nsfw_net, output_layers=['prob'])
    except IOError:
        return "The URL is not a image file!"

    after_mode = time.time()
    # Scores is the array containing SFW / NSFW image probabilities
    # scores[1] indicates the NSFW probability
    if mode == 'simple':
        return json.dumps({
                'sfw_score': scores[0], 
                'nsfw_score':scores[1], 
                'ats_image_download':int((after_download_image-begin)*1000), 
                'ats_model_predict':int((after_mode-after_download_image)*1000)}
            )
    else:
        return render(url, scores, (after_download_image-begin)*1000, (after_mode-after_download_image)*1000)

@route('/hello')
def hello():
    return "Hello World!\n"

def render(url, scores, ats_image_download, ats_model_predict):
    return template(
        '''
            <div>
                <img src="{{url}}" style="width:500px">
            </div>
            <ul> 
                <li>sfw_score: {{sfw_score}}</li>
                <li>nsfw_score: {{nsfw_score}}</li>
                <li>ats_image_download: {{ats_image_download}}</li>
                <li>ats_model_predict: {{ats_model_predict}}</li>
            </ul>
        ''', 
        url = url, 
        sfw_score="%.6f" % scores[0], 
        nsfw_score="%.6f" % scores[1], 
        ats_image_download="%.6f" % ats_image_download, 
        ats_model_predict="%.6f" % ats_model_predict
        )

if __name__ == '__main__':
    pycaffe_dir = os.path.dirname(__file__)
    run(host='0.0.0.0', port=8080, debug=True)
