import random
import numpy
from mnist import MNIST


class Neuron:

    def __init__(self, layer_number, node_number, bias):
        self.layer_number = layer_number
        self.node_number = node_number
        self.bias = bias
        self.activation = 0
        self.error = 0
        self.mini_batch_error_sum = 0
        self.mini_batch_error_activation_sum = 0
        self.z = 0
        # neurons are stored in an array
        # the index of the neurons in the previous layer is used as the key for this dictionary
        # the value of the dict entries is a pair of activation value and weight from the previous layer
        # this could maybe be streamlined
        self.input_neurons = []

    # adds a neuron to the dictionary of inputs
    def establish_input_neuron(self, weight):
        # defaults input value to 0
        # index 2 is used to sum the product of error in current node and activation value of previous node
        # to aid calculation when updating weights with gradient descent
        self.input_neurons.append([0, weight, 0])

    # with the neuron ids outputted from the function above, their output values are obtained and pushed back
    # into this object with this function.
    def set_input_activation(self, neuron_id, activation):
        self.input_neurons[neuron_id][0] = activation

    # once all inputs are collected they can be processed
    def process_inputs(self):
        # sigmoid function
        summation = self.bias
        for input_node in self.input_neurons:
            summation += input_node[0] * input_node[1]
        # set z for later use
        self.z = summation
        # 1 / (1 + e^-z)
        if self.z > 100:
            print("z value huge:", self.z)
        self.activation = numpy.float128(1 / (1 + numpy.exp(-self.z)))

    def get_activation(self):
        return self.activation


# adds set_value method specifically for neurons in the first layer
class InputNeuron(Neuron):

    def set_activation(self, activation):
        self.activation = activation


class NeuralNet:

    def __init__(self, input_size, output_size):
        # create network structure

        self.learning_rate = 1.0
        # first layer is an input layer so number of neurons equals dataset size
        self.layers = (input_size, 30, output_size)

        # express neural_net as 2D list
        self.network = [[] for layer in self.layers]

        self.output_vector = []

        # iterate through each layer
        for layer_id in range(0, len(self.layers)):
            # iterate through each node in layer
            for node_id in range(0, self.layers[layer_id]):
                # if input layer, create InputNeurons that can have their value manually set
                if layer_id == 0:
                    node = InputNeuron(layer_id, node_id, numpy.random.rand())
                # otherwise set number of inputs equal to number of nodes in previous layer
                else:
                    node = Neuron(layer_id, node_id, numpy.random.rand())

                    # connect each node to every node in the previous layer
                    for input_node_id in range(0, self.layers[layer_id-1]):
                        # randomise weight
                        node.establish_input_neuron(numpy.random.rand())

                # add node to neural net list
                self.network[layer_id].append(node)

    def pass_data(self, sample):
        # pass data through network

        # feed data to first layer
        for i in range(0, len(sample)):
            # set values for input layer
            self.network[0][i].set_activation(sample[i])

        # iterate through each layer after input layer
        for layer_id in range(1, len(self.network)):
            # iterate through each neuron in layer
            for neuron in self.network[layer_id]:
                # get data from previous layer
                # for each neuron from the previous layer (all of which input to the current node from above)
                for input_neuron in self.network[layer_id-1]:
                    # get the outputted value from node in previous layer
                    # and set the input value for this node
                    neuron.set_input_activation(input_neuron.node_number, input_neuron.activation)

                # apply sigmoid to inputted data
                neuron.process_inputs()

                # if in output layer, add value to output_vector
                if layer_id == len(self.network)-1:
                    self.output_vector.append(neuron.get_activation())

    def gradient_descent(self, data, num_epochs, mini_batch_size):
        # for each epoch
        for i in range(0, num_epochs):
            # shuffle data to divide it differently in each epoch
            random.shuffle(data)

            # divide randomised dataset into equally-sized mini batches
            mini_batches = []
            k = 0
            while k < len(data):
                # adds mini_batches of size mini_batch_size
                # if len(data) % mini_batch_size != 0 then the last data items are ignored
                mini_batches.append(data[k:k+mini_batch_size])
                k += mini_batch_size

            for mini_batch in mini_batches:
                print("epoch ", i, " mini batch", mini_batches.index(mini_batch))

                # each sample has format (x, y) where x is a list of pixel values for the 28x28 image and y is label
                for sample in mini_batch:
                    #max_val = max(sample[0])
                    #print("epoch ", i, " mini batch", mini_batches.index(mini_batch), "sample", mini_batch.index(sample), "max value", max_val)

                    # backpropagate
                    self.backprop(sample[0], sample[1])

                    # iterate through forwards, ignoring input layer
                    for layer_num in range(1, len(self.network)):
                        for neuron in self.network[layer_num]:
                            # use the current network state to add to the error/activation sums
                            # used in calculating the changes in weight/bias after mini batch is wholly fed through
                            neuron.mini_batch_error_sum += neuron.error
                            for i in range(0, len(neuron.input_neurons)):
                                # set the error/activation product sum value as the product of this neuron's error
                                # and the activation of the neuron associated with this weight, from the prev layer
                                neuron.input_neurons[i][2] += neuron.error * self.network[layer_num-1][i].activation

                # once mini batch has been fed through network
                # iterate through every neuron in every layer
                for layer in self.network:

                    for neuron in layer:

                        # calculate quantity to change bias by:
                        # the product of the mean of its errors and the learning rate
                        bias_delta = neuron.mini_batch_error_sum * self.learning_rate / mini_batch_size
                        neuron.bias -= bias_delta

                        # adjust each weight
                        for input_neuron in neuron.input_neurons:
                            # calculate mean of products of error in secondary neuron and activation in primary neuron
                            # multiply by learning rate
                            weight_delta = input_neuron[2] * self.learning_rate / mini_batch_size
                            input_neuron[1] -= weight_delta

    def backprop(self, x, y):

        # pass input x through network
        self.pass_data(x)

        # calculate error in output layer
        for neuron in self.network[-1]:
            # if the node number in the output layer matches label (e.g. if this is node 8 and label is 8)
            if neuron.node_number == y:
                # this neuron should fire fully
                expected_value = 1
            else:
                # otherwise we seek it to be completely off
                expected_value = 0
            neuron.error = (neuron.activation - expected_value) * self.sigmoid_prime(neuron.z)

        # propagate backwards through each layer the precedes the output layer:
        for l in range(2, len(self.network)):
            # for each neuron in layer -l
            for neuron in self.network[-l]:
                sum = 0
                # for each neuron in next layer
                for successive_neuron in self.network[1-l]:
                    # multiplies the next-layer neuron's error
                    # by the weight connecting it to the neuron in the CURRENT layer
                    # recall that weights between two nodes are stored in the node that appears later in the network
                    # (e.g. weight between a pair of neurons in layers 1 and 2 is stored in the node in layer 2)
                    sum += successive_neuron.error * successive_neuron.input_neurons[neuron.node_number][1]
                # update the current neuron's error
                neuron.error = sum * self.sigmoid_prime(neuron.z)

    def sigmoid_prime(self, z):
        return numpy.float128(1.0 / (1.0 + numpy.exp(-z)))

    def output_result(self):
        for x in self.output_vector:
            print(x)

    """
    def cost(self, f, y):
        # f is network output, y is desired output
        sum = 0
        for i in range(0, len(f)):
            sum += (f - y)**2
        cost = sum / (2)
        return cost
    """

    def choose_output(self):
        highest_activation = [0, 0]
        for neuron in self.network[-1]:
            if neuron.activation > highest_activation[1]:
                highest_activation = [neuron.node_number, neuron.activation]
        return highest_activation

    def test_network(self, data):

        random.shuffle(data)
        correctly_identified = 0
        for sample in data:
            self.pass_data(sample)
            if self.choose_output()[0] == sample[1]:
                correctly_identified += 1

        print(correctly_identified)


# use python-mnist module to read data from local files
mndata = MNIST('data')

data = []
training_images, training_labels = mndata.load_training()
testing_images, testing_labels = mndata.load_testing()
# zip two arrays in a single list of tuples (x, y), where x is an array containing pixel values for the image
#   and y is an integer of 0-9 - the image label
training_data = list(zip(training_images, training_labels))
testing_data = list(zip(testing_images, testing_labels))


print(training_data[0])

network = NeuralNet(784, 10)
network.gradient_descent(training_data, 30, 10)
#network.test_network(testing_data)

""""
# cost function
summation = 0
for sample in samples:
    # find vector difference between expected and real outcome
    vector_difference = []
    # for each output value
    for i in range(0, len(sample[1])):
        # find difference between expected and actual output value, put this in a difference vector
        vector_difference.append(sample[1][i] - sample[2][i])

    # find square magnitude by doing pythagoras and square rooting, then square again
    # last two steps cancel out so just find sum of squares
    square_sum = 0

    for x in vector_difference:
        square_sum += x**2

    summation += square_sum

cost = summation / (2 * number_samples)

print(cost)
"""
