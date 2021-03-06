# -*- coding: utf-8 -*-
"""
base models of Residual Attention Network
"""

import tensorflow as tf


class Layer(object):
    """basic layer"""
    def __init__(self, shape):
        """
        initial layer
        :param shape: shape of weight  (ex: [input_dim, output_dim]
        """
        # Xavier Initialization
        self.W = self.weight_variable(shape)
        self.b = tf.Variable(tf.zeros([shape[1]]))

    @staticmethod
    def weight_variable(shape, name=None):
        """define tensorflow variable"""
        # 標準偏差の2倍までのランダムな値で初期化
        initial = tf.truncated_normal(shape, stddev=0.1)
        return tf.Variable(initial, name=name)

    def f_prop(self, x):
        """forward propagation"""
        return tf.matmul(x, self.W) + self.b


class Dense(Layer):
    """softmax layer """
    def __init__(self, shape, function=tf.nn.softmax):
        """
        :param shape: shape of weight (ex:[input_dim, output_dim]
        :param function: activation ex:)tf.nn.softmax
        """
        super().__init__(shape)
        # Xavier Initialization
        self.function = function

    def f_prop(self, x):
        """forward propagation"""
        return self.function(tf.matmul(x, self.W) + self.b)


class Conv(Layer):
    """Convolution layer"""
    def __init__(self, shape, strides=[1, 2, 2, 1], padding="SAME"):
        """
        :param shape: shape of filter weight (ex:[row of filter, line of filter , input channel, output channel]
        :param strides: strides of kernel
        :param padding: padding type ["SAME", "VALID"]
        """
        self.W = self.weight_variable(shape)
        self.b = tf.Variable(tf.zeros([shape[3]]))
        self.strides = strides
        self.padding = padding

    def f_prop(self, x):
        """forward propagation"""
        conv = tf.nn.conv2d(x, filter=self.W, strides=self.strides, padding=self.padding)
        return conv


class BatchNormalization(Layer):
    """
    batch normalization
    """
    def __init__(self, channels, variance_epsilon=0.001, scale_after_normalization=True):
        """
        :param channels: channels of input data
        :param variance_epsilon:  A small float number to avoid dividing by 0
        :param scale_after_normalization: A bool indicating whether the resulted tensor needs to be multiplied with gamma
        """
        self.channels = channels
        self.variance_epsilon = variance_epsilon
        self.scale_after_normalization = scale_after_normalization
        self.beta = tf.Variable(tf.zeros([self.channels]), name="beta")
        self.gamma = self.weight_variable([self.channels], name="gamma")

    def f_prop(self, x):
        """
        batch normalization
        :param x: input x
        :return: batch normalized x
        """
        mean, var = tf.nn.moments(x, axes=[0, 1, 2])

        batch_norm = tf.nn.batch_norm_with_global_normalization(
            x, mean, var, self.beta, self.gamma, self.variance_epsilon,
            scale_after_normalization=self.scale_after_normalization)

        # relu
        return tf.nn.relu(batch_norm)


class ResidualBlock(object):
    """residual block proposed by https://arxiv.org/pdf/1603.05027.pdf"""
    def __init__(self, input_channels, output_channels=None, stride=1):
        """
        :param input_channels: dimension of input channel.
        :param output_channels: dimension of output channel. input_channel -> output_channel
        """
        self.input_channels = input_channels
        if output_channels is not None:
            self.output_channels = output_channels
        else:
            self.output_channels = input_channels
        self.stride = stride
        # graph
        self.batch_normalization = BatchNormalization(self.input_channels)
        self.conv1 = Conv([3, 3, self.input_channels, self.output_channels], strides=[1, 1, 1, 1])
        self.batch_normalization_2 = BatchNormalization(self.output_channels)
        self.conv2 = Conv([3, 3, self.output_channels, self.output_channels], strides=[1, stride, stride, 1])

        self._conv = Conv([1, 1, self.input_channels, self.output_channels], strides=[1, stride, stride, 1])

    def f_prop(self, x):
        """
        forward propagation
        :param x: input x
        :return: output residual block
        """

        # batch normalization & ReLU
        batch_normed_output = self.batch_normalization.f_prop(x)

        # convolution1: change channels
        output_conv1 = self.conv1.f_prop(batch_normed_output)

        # batch normalization & ReLU
        batch_normed_output = self.batch_normalization_2.f_prop(output_conv1)

        # convolution2
        output_conv2 = self.conv2.f_prop(batch_normed_output)

        if (self.input_channels != self.output_channels) or (self.stride!=1):
            input_layer = self._conv.f_prop(x)
        else:
            input_layer = x

        res = output_conv2 + input_layer
        return res
