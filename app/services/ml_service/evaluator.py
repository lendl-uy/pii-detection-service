from sklearn.metrics import fbeta_score

class Evaluator:

    def __init__(self, f5_threshold):
        self.f5_threshold = f5_threshold
        self.f5_score = None

    def __evaluate(self, Y_true, Y_pred):
        f5_score = fbeta_score(Y_true, Y_pred, beta=5, average="micro")
        self.f5_score = f5_score

    def check_for_model_drift(self, Y_true, Y_pred):
        self.__evaluate(Y_true, Y_pred)
        if self.f5_score < self.f5_threshold:
            return True
        return False