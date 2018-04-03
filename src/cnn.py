import tensorflow as tf

a = 10000

class CNN(object):
    def __init__(self, vocab_size, embedding_size, seq_length, filter_sizes, num_filters):
        self.input_x_a = tf.placeholder(shape=[None, seq_length], dtype=tf.int32, name="input_x_a")
        self.input_x_b = tf.placeholder(shape=[None, seq_length], dtype=tf.int32, name="input_x_b")
        self.input_y = tf.placeholder(shape=[None], dtype=tf.int32, name="input_y")
        self.batch_size = tf.placeholder(dtype=tf.int32, name="batch_size")
        self.dropout_keep_prob = tf.placeholder(dtype=tf.float32, name="dropout_keep_prob")

        with tf.variable_scope("embedding_matrix"):
            self.embedding_matrix = tf.get_variable(shape=[vocab_size, embedding_size], dtype=tf.float32,
                                                    name="embedding_matrix", trainable=False)
            self.embedding_chars_a = tf.nn.embedding_lookup(params=self.embedding_matrix, ids=self.input_x_a)
            self.embedding_chars_b = tf.nn.embedding_lookup(params=self.embedding_matrix, ids=self.input_x_b)
            self.pairs = tf.concat([self.embedding_chars_a, self.embedding_chars_b], axis=0)
            self.pairs = tf.expand_dims(self.pairs, -1)

        pooled_output = []
        with tf.variable_scope("convolution"):
            for filter_size in filter_sizes:
                filter_shape = [filter_size, embedding_size, 1, num_filters]
                W = tf.Variable(tf.truncated_normal(filter_shape, stddev=0.1), name="W")
                b = tf.Variable(tf.constant(0.1, shape=[num_filters]), name="b")
                conv = tf.nn.conv2d(self.pairs, filter=W, strides=[1, 1, 1, 1],
                                    padding='VALID', name='conv')
                h = tf.nn.relu(tf.nn.bias_add(conv, b), name='relu')
                pooled = tf.nn.max_pool(h, ksize=[1, seq_length - filter_size + 1, 1, 1], strides=[1, 1, 1, 1],
                                        padding="VALID", name="pooling")
                pooled_output.append(pooled)

        num_filter_total = num_filters * len(filter_sizes)
        h_pool = tf.concat(pooled_output, 3)
        flatten = tf.reshape(h_pool, shape=[-1, num_filter_total])

        self.outputs_a = flatten[:self.batch_size]
        self.outputs_b = flatten[self.batch_size:]
        self.outputs = tf.concat([self.outputs_a, self.outputs_b], axis=1)
        # batch normalization
        self.normalized = tf.layers.batch_normalization(self.outputs)
        with tf.variable_scope("output"):
            # self.manhattan_dist = tf.reduce_sum(tf.abs(self.outputs_a - self.outputs_b), axis=1, name="dist")
            # self.predictions = tf.exp(-self.manhattan_dist, name="predictions")
            # self.loss = tf.reduce_sum(tf.losses.mean_squared_error(labels=self.input_y, predictions=self.predictions),
            #                           name="loss")
            #
            # predictions = tf.cast(self.predictions > 0.5, "float")
            w_softmax = tf.get_variable(shape=[num_filter_total * 2, 2],
                                        initializer=tf.contrib.layers.xavier_initializer(),
                                        name="w_softmax")
            b_softmax = tf.get_variable(shape=[2], initializer=tf.contrib.layers.xavier_initializer(), name="b_softmax")
            self.logits = tf.matmul(self.normalized, w_softmax) + b_softmax
            self.losses = tf.nn.sparse_softmax_cross_entropy_with_logits(logits=self.logits, labels=self.input_y)
            self.loss = tf.reduce_mean(self.losses)
            self.predictions = tf.argmax(self.logits, axis=1)
            correct_pred = tf.equal(self.predictions, tf.cast(self.input_y, tf.int64))
            self.acc = tf.reduce_mean(tf.cast(correct_pred, "float"))
