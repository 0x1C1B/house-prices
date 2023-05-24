"""
Module for training a linear regression model with ridge regularization.
"""

import argparse
import pandas as pd
import numpy as np
import joblib
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge
from sklearn.model_selection import RandomizedSearchCV
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, OrdinalEncoder
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from house_prices.modelling.feature_selection import get_ordinal_feature_names, get_binary_feature_names, get_numerical_feature_names, ORDINAL_FEATURE_MAPPINGS

# pylint: disable=unnecessary-lambda-assignment
vprint = lambda *a, **k: None

def build_model(df: pd.DataFrame):
  """
  Builds a linear regression model with ridge regularization.
  """

  vprint("Building model ...")

  ordinal_features = get_ordinal_feature_names(df)
  binary_features = get_binary_feature_names(df)
  numerical_features = get_numerical_feature_names(df)

  ordinal_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OrdinalEncoder(categories=[value for key, value in ORDINAL_FEATURE_MAPPINGS.items()], dtype=int)),
  ])

  binary_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore")),
  ])

  numerical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="mean")),
    ("scaler", StandardScaler()),
  ])

  transformer = ColumnTransformer([
    ("ordinal", ordinal_pipeline, ordinal_features),
    ("binary", binary_pipeline, binary_features),
    ("numerical", numerical_pipeline, numerical_features),
  ])

  estimator = TransformedTargetRegressor(regressor=Ridge(), func=np.log, inverse_func=np.exp)

  model = Pipeline([
    ("transformer", transformer),
    ("estimator", estimator),
  ])

  return model

def train_model(x: pd.DataFrame,
                y: pd.Series,
                param_distributions,
                n_iter=10,
                n_folds=10,
                n_jobs=None,
                verbose=0,
                random_state=42):
  """
  Trains a linear regression model with ridge regularization.
  """

  model = build_model(x)
  cv = RandomizedSearchCV(model, param_distributions, n_iter=n_iter, cv=n_folds,
                          n_jobs=n_jobs, verbose=verbose, random_state=random_state, return_train_score=True)

  vprint("Training model ...")

  cv.fit(x, y)

  return cv

def main():
  parser = argparse.ArgumentParser(prog="train_lm_ridge.py",
                                   formatter_class=argparse.RawTextHelpFormatter,
                                   description="Trains a linear ridge regression model.")

  parser.add_argument("-v", "--verbose", action="store_true",
                      help="Print out verbose messages.")
  parser.add_argument("-i", "--input", type=str, required=True,
                      help="Input file path of train set. Must be a CSV file.")
  parser.add_argument("-o", "--output", type=str, required=True,
                      help="Output file path. Must be a JOBLIB file.")

  args = parser.parse_args()

  if args.verbose:
    global vprint
    vprint = print

  vprint(f"Loading data from '{args.input}' ...")

  df = pd.read_csv(args.input)

  hyperparameters = {
    "estimator__regressor__alpha": np.logspace(-3, 3, 50),
  }

  model = train_model(df.drop("SalePrice", axis=1), df["SalePrice"], hyperparameters,
                      verbose=5 if args.verbose else 0, n_jobs=-2, n_iter=20)

  vprint(f"Saving model to '{args.output}' ...")

  joblib.dump(model, args.output)

if __name__ == "__main__":
  main()
