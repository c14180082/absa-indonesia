from feature_extractor import FeatureExtractor
from item_selector import ItemSelector
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.multiclass import OneVsRestClassifier
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.externals import joblib
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, classification_report, confusion_matrix
import numpy as np
import csv, re

class CategoryExtractor:
    def __init__(self, train_filename):
        self.pipeline = Pipeline([
            ('data', FeatureExtractor()),

            ('features', FeatureUnion(
                transformer_list=[

                    ('bag_of_ngram', Pipeline([
                        ('selector', ItemSelector(key='sentence')),
                        ('ngram', CountVectorizer(ngram_range=(1, 2))),
                    ])),

                    ('bag_of_word2vec', Pipeline([
                        ('selector', ItemSelector(key='word2vec')),
                        ('ngram', CountVectorizer(ngram_range=(1, 2))),
                    ])),

                    ('bag_of_glove', Pipeline([
                        ('selector', ItemSelector(key='glove')),
                        ('ngram', CountVectorizer(ngram_range=(1, 2))),
                    ])),

                    ('bag_of_lda', Pipeline([
                        ('selector', ItemSelector(key='lda')),
                        ('ngram', CountVectorizer(ngram_range=(1, 2))),
                    ]))

                ]
            )),

            ('clf', OneVsRestClassifier(LogisticRegression()))
        ])
        self.target_names = ['food', 'service', 'price', 'place']
        train_data, self.train_target = self.read_data(train_filename)
        self.train_data = np.array(train_data)
        
        self.model_filename = "../../data/category_extraction/category_extractor.model"

    def read_data(self, filename):
        data = []
        targets = []
        regex = re.compile('[^0-9a-zA-Z]+')
        with open (filename, "rb") as f:
            reader = csv.reader(f, delimiter=';', quotechar='"')
            next(reader)
            for row in reader:
                data.append(regex.sub(' ', row[0]))
                target = []
                for i in range(1, len(self.target_names) + 1):
                    if (row[i] == "yes"):
                        target.append(self.target_names[i-1])
                targets.append(target)
        return data, targets

    def train(self):
        mlb = MultiLabelBinarizer()
        labels = mlb.fit_transform(self.train_target)

        model = self.pipeline.fit(self.train_data, labels)
        joblib.dump(self.pipeline.fit(self.train_data, labels), self.model_filename)

    def evaluate_cross_validation(self):
        mlb = MultiLabelBinarizer()
        labels = mlb.fit_transform(self.train_target)
        n = 10
        X_folds = np.array_split(self.train_data, n)
        y_folds = np.array_split(labels, n)

        precision_scores = []
        recall_scores = []
        f1_scores = []

        for k in range(n):
            X_train = list(X_folds)
            X_test  = X_train.pop(k)
            X_train = np.concatenate(X_train)
            y_train = list(y_folds)
            y_test  = y_train.pop(k)
            y_train = np.concatenate(y_train)

            model = self.pipeline.fit(X_train, y_train)
            predicted = self.pipeline.predict(X_test)

            # print classification_report(y_test, predicted, target_names=self.target_names)

            precision_scores.append(precision_score(y_test, predicted, average=None).mean())
            recall_scores.append(recall_score(y_test, predicted, average=None).mean())
            f1_scores.append(f1_score(y_test, predicted, average=None).mean())

        print "Precision: ", np.array(precision_scores).mean()
        print "Recall: ", np.array(recall_scores).mean()
        print "F1-score: ", np.array(f1_scores).mean()

    def evaluate(self, test_filename):
        # self.train()
        model = joblib.load(self.model_filename)
        test_data, test_target = self.read_data(test_filename)
        test_data = np.array(test_data)

        mlb = MultiLabelBinarizer()
        labels = mlb.fit_transform(test_target)

        predicted = model.predict(test_data)

        print "Precision: ", precision_score(labels, predicted, average=None)
        print "Recall: ", recall_score(labels, predicted, average=None)
        print "F1-score: ", f1_score(labels, predicted, average=None)

        all_labels = mlb.inverse_transform(predicted)

        # with open("../../data/category_extraction/result_test_data_cumulative.csv", "wb") as f:
        #     writer = csv.writer(f, delimiter=';', quotechar='"')
        #     for item, labels in zip(test_data, all_labels):
        #         data = [item]
        #         for target_name in self.target_names:
        #             if target_name not in labels:
        #                 data.append("no")
        #             else:
        #                 data.append("yes")
        #         writer.writerow(data)


    def predict(self, test_data):
        model = joblib.load(self.model_filename)
        mlb = MultiLabelBinarizer()

        predicted = model.predict(test_data)
        all_labels = mlb.inverse_transform(predicted)

        for item, labels in zip(test_data, all_labels):
            print('{0} => {1}'.format(item, ', '.join(labels)))

if __name__ == '__main__':
    category_extractor = CategoryExtractor("../../data/category_extraction/train_data.csv")
    # category_extractor.train()
    # category_extractor.evaluate_cross_validation()
    category_extractor.evaluate("../../data/category_extraction/test_data.csv")
    category_extractor.evaluate("../../data/category_extraction/test_data_cumulative.csv")
    