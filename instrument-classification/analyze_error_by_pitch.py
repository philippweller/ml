import matplotlib as mpl
# do not use Qt/X that require $DISPLAY, must be called before importing pyplot
mpl.use('Agg')
import matplotlib.pyplot as plt

import pandas as pd
import numpy as np

from classify_instrument import InstrumentClassifier

import jsonpickle
import jsonpickle.ext.numpy as jsonpickle_numpy
jsonpickle_numpy.register_handlers()


data_dir = 'data/working/single-notes-2000/'
data = np.load(data_dir + '/ml-inputs/features_targets.npz')
x, y = data['x'], data['y']

classifier = InstrumentClassifier('data/working/single-notes-2000/model')
model = classifier.model

parameters_with_targets = pd.read_csv(data_dir + '/ml-inputs/parameters_with_targets.csv', index_col=0)


splits = pd.read_csv(data_dir + '/ml-inputs/splits.csv', index_col=0)

with open(data_dir + '/ml-inputs/splits.json', 'r') as f:
    ix = jsonpickle.decode(f.read())['indices']

data_points = parameters_with_targets.join(splits)


df_pred = pd.DataFrame({'class_pred': model.predict_classes(x)})

df_pred = pd.DataFrame(
    model.predict_proba(x),
    columns=['proba_' + l for l in classifier.instr_family_le.classes_])
df_pred['class_pred'] = model.predict_classes(x)
df_pred = df_pred.round(5)

data_points = data_points.join(df_pred)

data_points['correct_class'] = data_points['family_id'] == data_points['class_pred']

data_points.to_csv(data_dir + '/evaluation/predictions.csv')


# analyze error by pitch

correct_by_midi_valid = data_points[data_points['split'] == 'valid'][['midi_number', 'correct_class']]

df_error_by_midi_valid = pd.DataFrame(index=np.arange(128))
hist = correct_by_midi_valid.groupby(['midi_number', 'correct_class']).size().reset_index().set_index('midi_number')
df_error_by_midi_valid['correct'] = hist[hist['correct_class']][0]
df_error_by_midi_valid['incorrect'] = hist[~hist['correct_class']][0]
df_error_by_midi_valid.fillna(0, inplace=True)


df_error_by_midi_valid['bin'] = df_error_by_midi_valid.index.map(lambda i: (i // 8) * 8)
df_error_by_midi_valid['total'] = df_error_by_midi_valid['correct'] + df_error_by_midi_valid['incorrect']

df_error_by_midi_valid_bins = df_error_by_midi_valid.groupby('bin').sum()

df_error_by_midi_valid_bins['correct_perc'] = df_error_by_midi_valid_bins['correct'] / df_error_by_midi_valid_bins['total']
df_error_by_midi_valid_bins['incorrect_perc'] = df_error_by_midi_valid_bins['incorrect'] / df_error_by_midi_valid_bins['total']

df_error_by_midi_valid_bins.to_csv(data_dir + '/evaluation/error_by_midi_valid_bins.csv')

fig, axes = plt.subplots(ncols=2, figsize=(15,5))
df_error_by_midi_valid_bins[['correct', 'incorrect']].plot(
    kind='bar', stacked=True, color=['green', 'red'], ax=axes[0])
df_error_by_midi_valid_bins[['correct_perc', 'incorrect_perc']].plot(
    kind='bar', stacked=True, color=['green', 'red'], ax=axes[1])

plt.suptitle('Error (absolute, relative) by pitch bins')

plt.savefig(data_dir + '/evaluation/error_by_midi_valid_bins.pdf')