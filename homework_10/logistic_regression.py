import numpy as np
from scipy import sparse


class LogisticRegression:
    def __init__(self):
        self.w = None
        self.loss_history = None

    def train(self, X, y, learning_rate=1e-3, reg=1e-5, num_iters=100,
              batch_size=200, verbose=False):
        # Add a column of ones to X for the bias sake.
        X = LogisticRegression.append_biases(X)
        num_train, dim = X.shape
        if self.w is None:
            # lazily initialize weights
            self.w = np.random.randn(dim) * 0.01

        # Run stochastic gradient descent to optimize W
        self.loss_history = []
        for it in range(num_iters):
        # Sample batch_size elements from the training data
            indices = np.random.choice(num_train, batch_size, replace=True)
            X_batch = X[indices]
            y_batch = y[indices]

        # evaluate loss and gradient
            loss, gradW = self.loss(X_batch, y_batch, reg)
            self.loss_history.append(loss)

        # perform parameter update
            self.w -= learning_rate * gradW

            if verbose and it % 100 == 0:
                print('iteration %d / %d: loss %f' % (it, num_iters, loss))

        return self
    
           
    def predict_proba(self, X, append_bias=False):
        if append_bias:
            X = LogisticRegression.append_biases(X)
        # Compute the scores
        scores = X.dot(self.w)
        # Apply the sigmoid function
        y_proba = 1 / (1 + np.exp(-scores))

        return np.vstack((1 - y_proba, y_proba)).T


    def predict(self, X):
        y_proba = self.predict_proba(X, append_bias=True)
        y_pred = np.argmax(y_proba, axis=1)
        return y_pred

    def loss(self, X_batch, y_batch, reg):
        num_train = X_batch.shape[0]
        scores = X_batch.dot(self.w)
        y_proba = 1 / (1 + np.exp(-scores))

        # Compute the loss
        loss = -np.mean(y_batch * np.log(y_proba + 1e-15) + (1 - y_batch) * np.log(1 - y_proba + 1e-15))
        loss += reg * np.sum(self.w[1:] ** 2)  # Regularization (excluding bias term)

        # Compute the gradient
        dw = X_batch.T.dot(y_proba - y_batch) / num_train
        dw[1:] += reg * self.w[1:]  # Regularization (excluding bias term)

        return loss, dw

    @staticmethod
    def append_biases(X):
        if not sparse.issparse(X):
            X = sparse.csr_matrix(X)
        return sparse.hstack((np.ones((X.shape[0], 1), dtype=X.dtype), X)).tocsr()
