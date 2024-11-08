import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Input
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.layers import Dropout
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

import pandas as pd

class PositionRegressor:
    """
    Class to train a neural network to predict the eye position based on the eye gaze vector.
    The backend of the neural network is a feedforward neural network with 3 hidden layers. Using TensorFlow and Keras.
    For training the network, the data has to be loaded from a csv file with the following columns:
    """
    def __init__(self, data_path):
        """
        Loads the data from the csv file and initializes the scaler for the input and output data.
        these scalers are used to normalize the data before training the neural network. and also normalize the predictions.
        :param data_path:
        """
        self.data_path = data_path
        self._model = None
        self._scaler_X = StandardScaler()
        self._scaler_y = StandardScaler()
        self.load_data()

    def load_data(self):
        try:
            data = pd.read_csv(self.data_path)
            print(data.shape)
            X = data[['l_x', 'l_y', 'l_z', 'r_x', 'r_y', 'r_z']].values
            y = data[['x', 'y']].values

            X = self._scaler_X.fit_transform(X)
            y = self._scaler_y.fit_transform(y)

            self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        except FileNotFoundError:
            raise FileNotFoundError("The file does not exist")

    def __create_model(self):
        """
        Creates the neural network model with 3 hidden layers and 1 output layer. For the prediction of the x and y
        from the gaze vector.
        :return: The new created and compiled model
        """
        model = Sequential([
            Input(shape=(6,)),
            Dense(64, activation='relu'),
            Dropout(0.01),
            Dense(32, activation='relu'),
            Dropout(0.01),
            Dense(16, activation='relu'),
            Dense(2)  # Output layer with 2 neurons for x and y coordinates
        ])
        model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        return model

    def train_create_model(self):
        """
        Trains the model with the training data and validates it with the test data. The training stops when the validation
        loss does not decrease for 5 epochs. Also stores the best weights of the model. The maximum epochs are set to 100.
        :return: the trained model and the history of the training.
        """
        self._model = self.__create_model()
        early_stopping = EarlyStopping(patience=5, restore_best_weights=True)
        history = self._model.fit(self.X_train, self.y_train, validation_data=(self.X_test, self.y_test), epochs=100, callbacks=[early_stopping])
        return self._model, history

    def make_prediction(self, data):
        """
        If the model is already created, makes a prediction with the given data. The data has to be a list of lists with
        the gaze vector data. The prediction is normalized and is transformed back to the original scale.
        :param data: The data from the gaze vector.
        :return: The predicted x and y coordinates of the screen.
        """
        if self._model is None:
            raise RuntimeError("Model not trained yet")

        # if len(data.shape) == 1:
        #     data = np.array([data])
        #     data = data.reshape(1, -1)

        data = self._scaler_X.transform(data)
        prediction = self._model.predict(data, verbose=0)
        predicted_original = self._scaler_y.inverse_transform(prediction)
        print(predicted_original)

        return predicted_original
