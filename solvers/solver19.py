import re
import os
import random
import time

import numpy as np
import tensorflow as tf
from keras_bert import load_trained_model_from_checkpoint
from solvers import tokenization
from solvers.punctuation_bert import PunctuationBert
from solvers.utils import AbstractSolver


class Solver(AbstractSolver):

    def __init__(self, seed=42, data_path='data/'):
        self.is_train_task = False
        self.seed = seed
        self.init_seed()

        self.tokenizer = None
        self.model_path = '/home/data/punctuation-bert'
        self.PunctuationBert = PunctuationBert(self.model_path)

    def init_seed(self):
        random.seed(self.seed)

    def predict(self, task):
        return self.predict_from_model(task)

    def process_task(self, task):
        task_text = re.split(r'\n', task['text'])
        sentence = task_text[1:-1]
        for s in task_text:
            if bool(re.search(r'(1)', s)):
                sentence = s
        return sentence

    def fit(self, tasks):
        pass

    def load(self, path="/home/data/punctuation-bert"):
        vocab_path = self.model_path + '/vocab.txt'
        self.tokenizer = tokenization.FullTokenizer(vocab_file=vocab_path, do_lower_case=False)

        print('Loading punctuation-bert model...')
        self.PunctuationBert.start()
        print('OK')

    def save(self, path):
        pass

    def predict_from_model(self, task):
        sentence = ""
        if task != None:
            sentence = self.process_task(task)

        sentence = re.sub(r'\d', '[PMASK]', sentence)
        sentence = sentence.replace('(', '').replace(')', '')

        sentence = sentence.replace(' [PMASK] ', '[PMASK]')
        sentence = sentence.replace('[PMASK] ', '[PMASK]')
        sentence = sentence.replace(' [PMASK]', '[PMASK]')
        sentence = sentence.split('[PMASK]')
        tokens = ['[CLS]']
        for i in range(len(sentence)):
            if i == 0:
                tokens = tokens + self.tokenizer.tokenize(sentence[i])
            else:
                tokens = tokens + ['[PMASK]'] + self.tokenizer.tokenize(sentence[i])
        tokens = tokens + ['[SEP]']

        token_input = self.tokenizer.convert_tokens_to_ids(tokens)
        token_input = token_input + [0] * (512 - len(token_input))

        mask_input = [0] * 512
        for i in range(len(mask_input)):
            if token_input[i] == 103 or token_input[i] == 2:
                mask_input[i] = 1

        seg_input = [0] * 512

        token_input = np.asarray([token_input])
        mask_input = np.asarray([mask_input])
        seg_input = np.asarray([seg_input])

        self.PunctuationBert.input = [token_input, seg_input, mask_input]
        while self.PunctuationBert.state != "waiting":
            time.sleep(0.1)
        predicts = self.PunctuationBert.output[0]
        self.PunctuationBert.output = None

        predicts = np.argmax(predicts, axis=-1)

        predicts = predicts[0][:len(tokens)]
        out = []
        for i in range(len(mask_input[0])):
            if mask_input[0][i] == 1:
                out.append(predicts[i])

        result = []
        for i in range(len(out)):
            if out[i] != 1:
                result.append(str(i + 1))

        return result
