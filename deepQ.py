import numpy as np
import random
import keras 
from keras.models import Sequential, load_model
from keras import optimizers
from keras.layers import Dense,Dropout,Activation
from keras.layers.advanced_activations import LeakyReLU
from keras.utils import plot_model
from keras import initializers



# from keras.callbacks import TensorBoard

# tensorboard = TensorBoard(log_dir='./logs', histogram_freq=0,
#                           write_graph=True, write_images=False)
# # define model
# model.fit(X_train, Y_train,
#           batch_size=batch_size,
#           epochs=nb_epoch,
#           validation_data=(X_test, Y_test),
#           shuffle=True,
#           callbacks=[tensorboard])

class NNQ:
	def __init__(self, inputs, outputs, discountFactor, learningRate):
		"""
		Parameters:
			- inputs: input size
			- outputs: output size
			- memorySize: size of the memory that will store each state
			- discountFactor: the discount factor (gamma)
			- learnStart: steps to happen before for learning. Set to 128
		"""
		self.input_size = inputs
		self.output_size = outputs
		self.discountFactor = discountFactor
		self.learningRate = learningRate

	def initNetworks(self, hiddenLayers):
		model = self.createModel(self.input_size, self.output_size, hiddenLayers, "sigmoid", self.learningRate)
		self.model = model


	def createModel(self, inputs, outputs, hiddenLayers, activationType, learningRate):
		model = Sequential()
		if len(hiddenLayers) == 0: 
			model.add(Dense(self.output_size, input_shape=(self.input_size,))  )
			model.add(Activation("linear"))
		else :
			model.add(Dense(hiddenLayers[0], input_shape=(self.input_size,)))
			if (activationType == "LeakyReLU") :
				model.add(LeakyReLU(alpha=0.01))
			else :
				model.add(Activation(activationType))
			
			for index in range(1, len(hiddenLayers)):
				# print("adding layer "+str(index))
				layerSize = hiddenLayers[index]
				model.add(Dense(layerSize))
				if (activationType == "LeakyReLU") :
					model.add(LeakyReLU(alpha=0.01))
				else :
					model.add(Activation(activationType))
			model.add(Dense(self.output_size, input_shape=(self.input_size,)))
			model.add(Activation("linear"))
		optimizer = optimizers.SGD(lr=0.01, clipnorm=1.)
		model.compile(loss="mse", optimizer=optimizer)

		# model.summary()
		return model

	def getQValues(self, state):
		# predicted = self.model.predict(state.reshape(1,len(state)))
		predicted = self.model.predict(state.reshape(1,len(state)))
		return predicted[0]

	def saveQValues(self,episode_num):
		f = open('Files/Qval.txt','a')
		print( '\nQ VALUES for ',episode_num,file = f)
		state = np.array([0,0,0])
		for i in range (0,4):
			for j in range(0,4):
				for k in range(0,4):
					state = np.array([i,j,k])
		# predicted = self.model.predict(state.reshape(1,len(state)))
					predicted = self.model.predict(state.reshape(1,len(state)))
					print(state,' -> ', predicted[0],file = f)

		f.close()
	
	def saveWeights(self,episode_num):
		f = open('Files/Wval.txt','a')
		print( '\nWeight VALUES for ',episode_num,file = f)
		for layer in self.model.layers:
			weights = layer.get_weights()
			print(weights,file = f)
	
	def selectAction(self, qValues, explorationRate):
		rand = random.random()
		if rand < explorationRate :
			action = np.random.randint(0, self.output_size)
			print("Random ",end="")
		else :
			action = self.getMaxIndex(qValues)
		print("action ",action)
		return action

	def saveModel(self, path):
		self.model.save(path)

	def loadWeights(self, path):
		self.model.set_weights(load_model(path).get_weights())

	def getMaxQ(self, qValues):
		return np.max(qValues)

	def getMaxIndex(self, qValues):
		return np.argmax(qValues)


	# def calculateTarget(self, qValuesNewState, reward, isFinal):
	# 	"""
	# 	target = reward(s,a) + gamma * max(Q(s')
	# 	"""
	# 	if isFinal:
	# 		return reward
	# 	else : 
	# 		return reward + self.discountFactor * self.getMaxQ(qValuesNewState)


	# def learn_on_one_example(self, state, action, reward, nextState, isFinal, mini_batch_size):
	# 	X_batch = np.empty((0,self.input_size), dtype = np.float64)
	# 	Y_batch = np.empty((0,self.output_size), dtype = np.float64)
		
	# 	X_batch = np.append(X_batch, np.array([state.copy()]), axis=0)
	# 	qValuesNewState = self.getQValues(nextState)
	# 	targetValue = self.calculateTarget(qValuesNewState, reward, isFinal)

	# 	qValues = self.getQValues(state)
	# 	Y_sample = qValues.copy()
	# 	Y_sample[action] = targetValue
	# 	Y_batch = np.append(Y_batch, np.array([Y_sample]), axis=0)

	# 	self.model.fit(X_batch, Y_batch, batch_size = mini_batch_size, epochs=30, verbose = 1, callbacks = [keras.callbacks.EarlyStopping(monitor='acc', min_delta=0, patience=0, verbose=1, mode='auto')])

	def learn_on_minbatch(self,training_set,mini_batch_size):
		# history = LossHistory()
		X_batch, Y_batch = self.process_training_set2(training_set,mini_batch_size)
		self.model.fit(
				X_batch, Y_batch, batch_size=mini_batch_size,
				epochs=1, verbose=0, 
			)
	def plotModel(self,path):
		plot_model(self.model, to_file=path+'Model.png')

	def process_training_set2(self,training_set,mini_batch_size):
	# by Microos, improve this batch processing function 
	#   and gain 50~60x faster speed (tested on GTX 1080)
	#   significantly increase the training FPS
	
	# instead of feeding data to the model one by one, 
	#   feed the whole batch is much more efficient

		mb_len = len(training_set)

		old_states = np.zeros(shape=(mb_len, 3))
		actions = np.zeros(shape=(mb_len,))
		is_final = np.zeros(shape=(mb_len,))
		rewards = np.zeros(shape=(mb_len,))
		new_states = np.zeros(shape=(mb_len, 3))

		for i, m in enumerate(training_set):
			old_state_m, action_m, reward_m, new_state_m,done = m
			old_states[i, :] = old_state_m[...]
			actions[i] = action_m
			rewards[i] = reward_m
			is_final[i] = done
			new_states[i, :] = new_state_m[...]

		old_qvals = self.model.predict(old_states, batch_size=mb_len)
		new_qvals = self.model.predict(new_states, batch_size=mb_len)

		maxQs = np.max(new_qvals, axis=1)
		y = old_qvals
		non_term_inds = np.where(is_final != True )[0]
		term_inds = np.where(is_final == True)[0]

		y[non_term_inds, actions[non_term_inds].astype(int)] = rewards[non_term_inds] + (self.discountFactor * maxQs[non_term_inds])
		y[term_inds, actions[term_inds].astype(int)] = rewards[term_inds]

		X_train = old_states
		y_train = y
		return X_train, y_train
