# -*- coding: utf-8 -*-
"""
Residual Attention Network
"""

import sys
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.utils import shuffle
from sklearn.metrics import f1_score
import tensorflow as tf
from keras.datasets import cifar10

from model.utils import EarlyStopping
from model.residual_attention_model import ResidualAttentionModel

# HYPER-PARAMETER
rng = np.random.RandomState(1234)
random_state = 42
NUM_EPOCHS = 100
BATCH_SIZE = 64
SAVE_PATH = "~/residual-attention-network/trained_models/model.ckpt"


if __name__ == "__main__":
    print("start to train ResidualAttentionModel")

    param = sys.argv
    if len(param) == 2:
        target_dataset = param[1]
        if target_dataset == "CIFER-10":
            raise ValueError("Now you can use only 'CIFER-10' for training. "
                             "Please specify valid DataSet {'CIFER-10'} or "
                             "write build_model method in ResidualAttentionModel class by yourself.")

    else:
        target_dataset = "CIFER-10"

    print("load {dataset} data...".format(dataset=target_dataset))
    if target_dataset == "CIFER-10":
        (cifar_X_1, cifar_y_1), (cifar_X_2, cifar_y_2) = cifar10.load_data()
        cifar_X = np.r_[cifar_X_1, cifar_X_2]
        cifar_y = np.r_[cifar_y_1, cifar_y_2]

        cifar_X = cifar_X.astype('float32') / 255
        cifar_y = np.eye(10)[cifar_y.astype('int32').flatten()]

        train_X, test_X, train_y, test_y = train_test_split(cifar_X, cifar_y, test_size=5000,
                                                            random_state=random_state)
        train_X, valid_X, train_y, valid_y = train_test_split(train_X, train_y, test_size=5000,
                                                              random_state=random_state)
    elif target_dataset == "ImageNet":
        # TODO(write code to load DataSet for ImageNet)
        print("TODO(load DataSet for ImageNet)")

    else:
        raise ValueError("Now you can use only 'CIFER-10' for training. "
                         "Please specify valid DataSet {'CIFER-10'} or "
                         "write build_model method in ResidualAttentionModel class by yourself.")

    print("build graph...")
    model = ResidualAttentionModel()
    model.build_model(target=target_dataset)
    early_stopping = EarlyStopping()

    x = tf.placeholder(tf.float32, [None, 32, 32, 3])
    t = tf.placeholder(tf.float32, [None, 10])

    y = model.f_props(x)

    loss = tf.nn.softmax_cross_entropy_with_logits(logits=y, labels=t)
    # self.cross_entropy = tf.reduce_mean(-tf.reduce_sum(y_ * tf.log(y), reduction_indices=[1]))
    train = tf.train.AdamOptimizer(1e-4).minimize(tf.reduce_mean(loss))
    valid = tf.argmax(y, 1)

    print("start to train...")
    with tf.Session() as sess:
        init = tf.global_variables_initializer()
        for epoch in range(NUM_EPOCHS):
            train_X, train_y = shuffle(train_X, train_y, random_state=random_state)
            # batch_train_X, batch_valid_X, batch_train_y, batch_valid_y = train_test_split(train_X, train_y, train_size=0.8, random_state=random_state)
            n_batches = train_X.shape[0] // BATCH_SIZE

            # train
            train_costs = []
            for i in range(n_batches):
                # print(i)
                start = i * BATCH_SIZE
                end = start + BATCH_SIZE
                _, loss = sess.run([train, loss],
                              feed_dict={x: train_X[start:end], t: train_y[start:end]})
                train_costs.append(loss)

            # valid
            valid_costs = []
            valid_predictions = []
            for i in range(n_batches):
                start = i * BATCH_SIZE
                end = start + BATCH_SIZE
                pred, valid_cost = sess.run([valid, loss], feed_dict={x: valid_X, t: valid_y})
                valid_predictions.extend(tf.argmax(pred, 1))
                valid_costs.append(valid_cost)

            score = f1_score(valid_y, valid_predictions, average='macro')
            if epoch % 5 == 0:
                print('EPOCH: {epoch}, Training cost: {train_cost}, Validation cost: {valid_cost}, Validation F1: {score}'.format(epoch=epoch, train_cost=np.mean(train_costs), valid_cost=np.mean(valid_costs), score=score))

            if early_stopping.check(np.mean(valid_costs)):
                print("save model...")
                saver = tf.train.Saver()
                saver.save(sess, SAVE_PATH, global_step=epoch)
                break













