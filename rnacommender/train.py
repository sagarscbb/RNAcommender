#!/usr/bin/env python

from __future__ import print_function
import argparse
import pandas as pd
import time
import cPickle

from data import TrainDataset
from model import Model

__author__ = "Gianluca Corrado"
__copyright__ = "Copyright 2016, Gianluca Corrado"
__license__ = "MIT"
__maintainer__ = "Gianluca Corrado"
__email__ = "gianluca.corrado@unitn.it"
__status__ = "Production"

class Trainer():
    """Train a model on a dataset"""
    def __init__(self,train_dataset,model,num_epochs,model_save,verbose=True):
        """
        Params
        ------
        train_dataset : data.TrainDataset
            Dataset containing the training examples.

        model : model.Model
            The initialized model.

        num_epochs : int
            Number of training epochs to perform

        model_save : str
            File name to save the trained model.

        verbose : bool (default : True)
            Print information at STDOUT.
        """

        self.train_dataset = train_dataset
        self.model = model
        self.epoch = 0
        self.num_epochs = num_epochs
        self.model_save = model_save
        self.verbose = verbose

    def _train_epoch(self):
        """Perform one train epoch"""
        start_time = time.time()
        for (P,R,I) in self.train_dataset:
            self.model.train(P,R,I)
        self.epoch += 1
        end_time = time.time()
        train_time = end_time - start_time
        return train_time

    def _test_epoch(self):
        """Compute the cost on the training set"""
        cumcost = 0.
        for (P,R,I) in self.train_dataset:
            y_hat,cost = self.model.test(P,R,I)
            cumcost += cost
        return cumcost

    def _print_monitor(self,cost,time=0.):
        """Monitoring step"""
        print("Epoch %i, cost: %f, elapsed time: %.1f sec" % (self.epoch,cost,time))

    def _save_model(self):
        """Dump a model to a pkl"""
        f = open(self.model_save,"w")
        cPickle.dump(self.model,f,protocol=2)
        f.close()
        print("Model saved to %s" % self.model_save)

    def train(self):
        """Train the model"""
        if self.verbose:
            cumcost = self._test_epoch()
            self._print_monitor(cumcost)

        while self.epoch < self.num_epochs:
            train_time = self._train_epoch()
            if self.verbose:
                cumcost = self._test_epoch()
                self._print_monitor(cumcost,train_time)

        self._save_model()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    # TrainDataset arguments
    parser.add_argument('Fp', metavar='Fp', type=str,
                        help="""HDF5 file with the protein features.""")
    parser.add_argument('Fr', metavar='Fr', type=str,
                        help="""HDF5 file with the RNA features.""")
    parser.add_argument('Y', metavar='Y', type=str,
                        help="""HDF5 file with interaction matrix.""")
    parser.add_argument('--standardize-Fp', dest='standardize_Fp', action='store_true', default=False,
                        help="""Standardize protein features.""")
    parser.add_argument('--standardize-Fr', dest='standardize_Fr', action='store_true', default=False,
                        help="""Standardize RNA features.""")

    # Model arguments
    parser.add_argument('--sp', metavar='sp', type=int, default=5,
                        help="""Size of the protein latent space.""")
    parser.add_argument('--sr', metavar='sr', type=int, default=50,
                        help="""Size of the RNA latent space.""")
    parser.add_argument('--learning-rate', metavar='learning_rate', type=float, default=1.0,
                        help="""Learning rate for the weights update.""")
    parser.add_argument('--lambda-reg', metavar='lambda_reg', type=float, default=1e-3,
                        help="""Lambda parameter for the regularization.""")

    # Trainer arguments
    parser.add_argument('--train-epochs', metavar='train_epochs', type=int, default=10,
                        help="""File name to save the trained model.""")
    parser.add_argument('--save-model', metavar='save_model', type=str, default=None,
                        help="""File name to save the trained model.""")

    # general arguments
    parser.add_argument('--quiet', dest='quiet', action='store_true', default=False,
                        help="""Silence STDOUT.""")
    parser.add_argument('--seed', metavar='seed', type=int, default=1234,
                        help="""Seed for random number gerator.""")

    args = parser.parse_args()

    def feature_size(store_name):
        """Number of features"""
        store = pd.io.pytables.HDFStore(store_name)
        a = store.features
        store.close()
        return a.shape[0]

    # Define model
    M = Model(n=feature_size(args.Fp),m=feature_size(args.Fr),
        sp=args.sp,sr=args.sr,learning_rate=args.learning_rate,lambda_reg=args.lambda_reg,
        verbose=(not args.quiet),seed=args.seed)

    # Define and instantiate dataset
    D = TrainDataset(Fp=args.Fp,Fr=args.Fr,Y=args.Y,
        standardize_proteins=args.standardize_Fp, standardize_rnas=args.standardize_Fr,
        verbose=(not args.quiet),seed=args.seed)
    dataset = D.load()

    # Define the Trainer and train the model
    T = Trainer(train_dataset=dataset,model=M,num_epochs=args.train_epochs,
        model_save=args.save_model,verbose=(not args.quiet))
    T.train()




