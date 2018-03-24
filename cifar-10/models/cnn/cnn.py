# Python 3

import os
import lzma
import math
import cv2
import numpy as np
import tensorflow as tf
from scipy import ndimage

tf.logging.set_verbosity(tf.logging.INFO)

CIFAR_DATA_FOLDER = 'data/'
"""
Directory includes:
    - sampleSubmission.csv
    - test.7z
    - train.7z
    - trainLabels.csv
"""

def cnn_model_fn(features, labels, mode):
    """Model function for CNN."""

    """Input Layer, i.e., the features or pixels of the image, reshaped to be a
    28x28 pixel image with a batch_size of `-1` which indicates the
    batch_size should be automatically determined. The number of channels is
    1, i.e., the number of color channels (in this case, img is monochrome)"""
    input_layer = tf.reshape(
        features["x"],  # data to reshape; our image features
        [-1, 32, 32, 3] # desired shape: [batch_size, width, height, channels]
    )

    # First Convolutional Layer; output shape = [batch_size, 28, 28, 32]
    # We will use 32 filters, 5x5 kernel size, 'same' padding, and relu
    ############################## YOUR CODE ##############################
    conv1 = tf.layers.conv2d(
        inputs = input_layer,
        filters = 32,
        kernel_size = [5, 5],
        padding = "same",
        activation = tf.nn.relu
    )

    # First Pooling Layer; output shape = [batch_size, 14, 14, 32]
    # 2x2 pool size with strides of 2
    ############################## YOUR CODE ##############################
    pool1 = tf.layers.max_pooling2d(
        inputs = conv1,
        pool_size = [2, 2],
        strides = 2
    )

    # Second Conv & Pooling Layers; output shape = [batch_size, 7, 7, 64]
    # 64 filters this time!
    ############################## YOUR CODE ##############################
    conv2 = tf.layers.conv2d(
        inputs = pool1,
        filters = 64,
        kernel_size = [5, 5],
        padding = "same",
        activation = tf.nn.relu
    )

    # max_pooling reduces our `image` width and height by 50%
    # 2x2 pool with strides of 2
    ############################## YOUR CODE ##############################
    pool2 = tf.layers.max_pooling2d(
        inputs = conv2,
        pool_size = [2, 2],
        strides = 2
    )

    # Flatten pool2 for input to dense layer; out_shape=[batch_size, 3136]
    pool2_flat = tf.reshape(pool2, [-1, 8 * 8 * 64])  # reshape to be flat (2D)

    # Performs the actual classification of the abstracted features from conv1/2
    # 512 nodes for this dense layer; ReLU activation
    ############################## YOUR CODE ##############################
    dense = tf.layers.dense(
        inputs = pool2_flat,
        units = 1024,
        activation = tf.nn.relu
    )

    # Dropout creates a chance that input is ignored during training. This will
    # decrease the chances of over-fitting the training data
    dropout = tf.layers.dropout(
        inputs=dense,          # inputs from the dense layer
        rate=0.5,              # randomly drop-out 40% of samples; keep 60%
        training=(mode == tf.estimator.ModeKeys.TRAIN)  # is training mode? T/F
    )
    # Output of dense layer, shape = [batch_size, 1024]

    """Final, logits layer giving us our outputs as probabilities of the original
    input image being a digit 0-9. Thus, we have a vector of 10 outputs which
    will each represent the probability for the input to be the digit. e.g.,
    if the first value, output[0] is high, then we say that the model predicts
    a high chance that the input was a handwritten digit '0'. This final layer
    is densely connected to the previous layer and provides 10 outputs. These
    outputs will later be turned into values from 0 to 1 representing actual
    probabilities (see predictions layer and tf.nn.softmax() below)
    Final shape: [batch_size, 10]"""
    logits = tf.layers.dense(inputs=dropout, units=10)


    predictions = {
        # Predicted class determined by finding the maximum value of the logits
        "classes": tf.argmax(input=logits, axis=1),  # get the predicted class

        # We get the normalize the probabilities to be from 0 to 1 with the sum
        # of all 10 equaling 1.0 by performing a softmax on the output vector.
        "probabilities": tf.nn.softmax(
            logits,                # softmax on logits (output of CNN)
            name="softmax_tensor"  # name for logging
        )
    }

    """If we are in prediction mode, return a predictor tensor of the network
    and stop; no more building required for prediction"""
    if mode == tf.estimator.ModeKeys.PREDICT:
        return tf.estimator.EstimatorSpec(mode=mode, predictions=predictions)

    """For TRAIN and EVAL modes, calculate the loss. Cross entropy is a loss
    technique commonly used when we have many classes to classify. This is
    just another function that calculates the error between our predicted
    class and the actual target class. The more wrong we are, the greater the
    loss is. e.g., predict 10% chance for a 5 and it is a 5 is bad; predict
    90% chance for a 5 and it is a 5 is better. Cross entropy is only
    concerned with the prediction accuracy for the target value."""
    # loss function here -- sparse-cross-entropy!
    ############################## YOUR CODE ##############################
    loss = tf.losses.sparse_softmax_cross_entropy(
        labels = labels,
        logits = logits
    )

    # Configure the training operation if TRAIN mode
    if mode == tf.estimator.ModeKeys.TRAIN:
        # We want a low learning rate so that we can slowly but surely reach
        # the optimum. Higher rates may learn faster but may overshoot the opt
        # Let's use a Gradient Descent Optimizer -- learning_rate of 0.06
        ############################## YOUR CODE ##############################
        optimizer = tf.train.GradientDescentOptimizer(learning_rate=0.001)

        # Use our Grad Descent optimizer to minimize the loss we calculated!
        train_op = optimizer.minimize(
            loss=loss,
            global_step=tf.train.get_global_step()
        )

        # return our estimator with the loss and train_op to train the model
        return tf.estimator.EstimatorSpec(
            mode=mode,
            loss=loss,
            train_op=train_op
        )

    # Add evaluation metrics for EVAL phase
    eval_metric_ops = {
        "accuracy": tf.metrics.accuracy(
            labels=labels,  # true labels given in data set
            predictions=predictions["classes"]  # predicted classes found above
        )
    }

    # return our estimator with the loss and eval_metric_ops to find accuracy
    return tf.estimator.EstimatorSpec(
        mode=mode,
        loss=loss,
        eval_metric_ops=eval_metric_ops
    )

def main(unused_argv):
    # Load training and eval data from MNIST set of handdrawn images
    # mnist = tf.contrib.learn.datasets.load_dataset("mnist")
    # train_data = mnist.train.images  # 55,000 images in this set!

    # train_labels = np.asarray(mnist.train.labels, dtype=np.int32)
    # eval_data = mnist.test.images  # 10,000 images here!
    # eval_labels = np.asarray(mnist.test.labels, dtype=np.int32)

    # Create the actual Estimator to run our model
    ############################## YOUR CODE ##############################
    cnn_classifier = tf.estimator.Estimator(
        model_fn = cnn_model_fn,
        model_dir='./cifar_cnn_model'
    )

    # Setup logging here
    tensors_to_log = {"probabilities": "softmax_tensor"} # prob from earlier
    logging_hook = tf.train.LoggingTensorHook(
        tensors=tensors_to_log,  # format {name-for-log: tensor-to-log}
        every_n_iter=100  # log every 50 steps of training
    )

    # Training the model
    train_input_fn = tf.estimator.inputs.numpy_input_fn(  # org. our inputs
        x={"x": train_data},  # set the feature data
        y=train_labels,       # set the truth labels
        batch_size=100,       # num samples to give at a time - orig: 100
        num_epochs=None,
        shuffle=True)         # randomize
    input_fn
    cnn_classifier.train(
        input_fn = train_input_fn,
        steps = 500,
        hooks=[logging_hook]
    )

    # Evaluate the model and print results!
    # Build the evaluate_input_function for giving the classifier our data
    eval_input_fn = tf.estimator.inputs.numpy_input_fn(
        x={"x": eval_data},
        y=eval_labels,
        num_epochs=1,
        shuffle=False)
    eval_results = cnn_classifier.evaluate(
        input_fn=eval_input_fn)  # evaluate based on the data!

    print(eval_results)

def evaluate_my_handwritten(mnist_classifier, logging_hook, data_folder):
    if not os.path.exists('new-data'):
        tar = tarfile.open('new-data.tar')
        tar.extractall()
        tar.close()

    images, labels = preprocess_my_handwritten(data_folder)

    eval_input_fn = tf.estimator.inputs.numpy_input_fn(
        x={"x": images},
        y=labels,
        shuffle=False
    )

    # evaluate based on the data!
    eval_results = cnn_classifier.evaluate(
        input_fn=eval_input_fn,
        hooks=[logging_hook]
    )

    print(eval_results)  # Print our results and accuracy!

def preprocess_my_handwritten(data_folder):

    # the folders to contain our data
    raw_filepath = os.path.join(data_folder, 'raw')
    proc_filepath = os.path.join(data_folder, 'proc')

    num_images = len(os.listdir(raw_filepath))

    # np.arrays that we will fill with out image/label data
    images = np.zeros((num_images, 784), dtype=np.float32)
    labels = np.zeros((num_images, 1), dtype=np.int32)

    # process each digit 0-9 one at a time
    i = 0
    for image_name in os.listdir(raw_filepath):
        label = image_name[0]
        if not label.isdigit():
            continue

        # load the image as a grayscale
        gray = cv2.imread(os.path.join(raw_filepath, image_name),
                          cv2.IMREAD_GRAYSCALE)

        # resize to 28x28 and invert to white writing on black background
        gray = cv2.resize(255-gray, (28, 28))

        # change gray to black if darker than a threshold
        (thresh, gray) = cv2.threshold(gray, 128, 255,
                                       cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        # Begin reformatting to center a 20x20 digit into a 28x28 box
        while np.sum(gray[0]) == 0:
            gray = gray[1:]
        while np.sum(gray[:,0]) == 0:
            gray = np.delete(gray,0,1)
        while np.sum(gray[-1]) == 0:
            gray = gray[:-1]
        while np.sum(gray[:,-1]) == 0:
            gray = np.delete(gray,-1,1)

        # handle resizing to 20x20
        rows, cols = gray.shape
        if rows > cols:
            factor = 20.0 / rows
            rows = 20
            cols = int(round(cols*factor))
            gray = cv2.resize(gray, (cols,rows))
        else:
            factor = 20.0 / cols
            cols = 20
            rows = int(round(rows*factor))
            gray = cv2.resize(gray, (cols, rows))

        # Now pad to add the black edges to make 28x28
        colsPadding = (int(math.ceil((28-cols)/2.0)),
                       int(math.floor((28-cols)/2.0)))
        rowsPadding = (int(math.ceil((28-rows)/2.0)),
                       int(math.floor((28-rows)/2.0)))
        gray = np.lib.pad(gray,(rowsPadding, colsPadding), 'constant')

        # Now center based on center of mass
        def getBestShift(img):
            cy,cx = ndimage.measurements.center_of_mass(img)

            rows,cols = img.shape
            shiftx = np.round(cols/2.0-cx).astype(int)
            shifty = np.round(rows/2.0-cy).astype(int)

            return shiftx,shifty

        def shift(img,sx,sy):
            rows,cols = img.shape
            M = np.float32([[1,0,sx],[0,1,sy]])
            shifted = cv2.warpAffine(img,M,(cols,rows))  # matrix transform
            return shifted

        # Apply shifting of inner box to be centered based on centerof mass
        shiftx, shifty = getBestShift(gray)
        shifted = shift(gray, shiftx, shifty)
        gray = shifted

        # save processed images
        if not os.path.exists(proc_filepath):
            os.mkdir(proc_filepath)
        cv2.imwrite(os.path.join(proc_filepath, image_name), gray)

        # scale 0 to 1
        flat = gray.flatten() / 255.0

        images[i] = flat
        labels[i] = label
        i += 1

    return images, labels

if __name__ == "__main__":
  tf.app.run()
