# Copyright 2017 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Read CIFAR-10 data from pickled numpy arrays and writes TFRecords.
Generates tf.train.Example protos and writes them to TFRecord files from the
python version of the CIFAR-10 dataset downloaded from
https://www.cs.toronto.edu/~kriz/cifar.html.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import argparse
import os
import cv2

import tarfile
from six.moves import cPickle as pickle
from six.moves import xrange  # pylint: disable=redefined-builtin
import tensorflow as tf

CIFAR_FILENAME = 'cifar-10-python.tar.gz'
CIFAR_DOWNLOAD_URL = 'https://www.cs.toronto.edu/~kriz/' + CIFAR_FILENAME
CIFAR_LOCAL_FOLDER = 'cifar-10-batches-py'


def download_and_extract(data_dir):
  # download CIFAR-10 if not already downloaded.
  tf.contrib.learn.datasets.base.maybe_download(CIFAR_FILENAME, data_dir,
                                                CIFAR_DOWNLOAD_URL)
  tarfile.open(os.path.join(data_dir, CIFAR_FILENAME),
               'r:gz').extractall(data_dir)


def _int64_feature(value):
  return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))


def _bytes_feature(value):
  return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


def _get_file_names():
  """Returns the file names expected to exist in the input_dir."""
  file_names = {}
  file_names['train'] = ['data_batch_%d' % i for i in xrange(1, 5)]
  file_names['validation'] = ['data_batch_5']
  file_names['eval'] = ['test_batch']
  return file_names


def read_pickle_from_file(filename):
  with tf.gfile.Open(filename, 'rb') as f:
    data_dict = pickle.load(f)
  return data_dict


def convert_to_tfrecord(input_files, output_file):
  """Converts a file to TFRecords."""
  def to_image(array):
    channels = np.split(array, 3)
    proc = []
    for i in xrange(len(channels[0])):
      for j in [0,1,2]:
        proc.append(channels[j][i])
    proc = np.array(proc)
    image = np.reshape(proc, (32, 32, 3))
    return image

  def to_array(image):
    proc = []
    for c in [0,1,2]:
      for x in xrange(len(image[0])):
        for y in xrange(len(image[0])):
          proc.append(image[x][y][c])
    array = np.array(proc)
    return array

  print('Generating %s' % output_file)
  with tf.python_io.TFRecordWriter(output_file) as record_writer:
    for input_file in input_files:
      data_dict = read_pickle_from_file(input_file)
      data = [data_dict['data'][8]]
      labels = [data_dict['labels'][8]]

      if 'test_batch' in input_file:
        print(labels)

        ctr = 0
        for image in data:
          images = []

          image = to_image(np.array(image))

          cv2.imwrite(os.path.join('censor_data', 'img_{}.png'.format(ctr)), image)
          images.append(to_array(image))  # start with original image

          # black out rectangles of the image to make sub imgs
          delta = [2, 2]  # [x, y] delta
          part_size = [32 // 4, 32 // 4]
          divisions = [(32 - part_size[0]) // delta[0], (32 - part_size[1]) // delta[1]]
          for i in xrange(divisions[0] + 1):
            for j in xrange(divisions[1] + 1):
              x = i * delta[0]
              y = j * delta[1]
              # (x, y) is the top left corner of the rectangle

              img = image.copy()

              for x_offset in xrange(part_size[0]):
                for y_offset in xrange(part_size[1]):
                  img[x + x_offset][y + y_offset] = [0, 0, 0]

              img = to_image(to_array(img))

              # cv2.imwrite(os.path.join('censor_data', 'img_{%02d}_{%02d}.png'.format(i,j)), img)
              images.append(to_array(img))

          for im in images:
            example = tf.train.Example(features=tf.train.Features(
                feature={
                    'image': _bytes_feature(im.tobytes()),
                    'label': _int64_feature(labels[ctr])
                }))
            record_writer.write(example.SerializeToString())

          ctr += 1

      # num_entries_in_batch = len(labels)
      # for i in range(num_entries_in_batch):
      #   example = tf.train.Example(features=tf.train.Features(
      #       feature={
      #           'image': _bytes_feature(data[i].tobytes()),
      #           'label': _int64_feature(labels[i])
      #       }))
      #   record_writer.write(example.SerializeToString())

def main(data_dir):
  print('Download from {} and extract.'.format(CIFAR_DOWNLOAD_URL))
  download_and_extract(data_dir)
  file_names = _get_file_names()
  input_dir = os.path.join(data_dir, CIFAR_LOCAL_FOLDER)
  for mode, files in file_names.items():
    input_files = [os.path.join(input_dir, f) for f in files]
    output_file = os.path.join(data_dir, mode + '.tfrecords')
    try:
      os.remove(output_file)
    except OSError:
      pass
    # Convert to tf.train.Example and write the to TFRecords.
    convert_to_tfrecord(input_files, output_file)
  print('Done!')


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--data-dir',
      type=str,
      default='',
      help='Directory to download and extract CIFAR-10 to.')

  args = parser.parse_args()
  main(args.data_dir)
