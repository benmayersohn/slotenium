import pandas as pd
from os import listdir
from os.path import isfile, join
import matplotlib.pyplot as plt 
import numpy as np

filedir = './results/siberian_storm/'
filenames = [filedir + f for f in listdir(filedir) if isfile(join(filedir, f))]

# Import
df = pd.concat((pd.read_csv(f) for f in filenames), axis=0, sort=False)
df = df.sort_values(by=['Time'])
print(df.head())

# Compute win as a fraction of wager
df = df[df['Wager'] > 0]
win_ratio = df['Win'] / df['Wager']

print(len(win_ratio))

# plot RTP evolution with number of simulations
_, ax = plt.subplots(1, 1)
means = win_ratio.expanding().mean()
ax.plot(np.arange(len(means)), means)
ax.set_title('RTP Evolution')
ax.set_xlabel('Simulation Number')
ax.set_yticks([1, 2, 3, 4, 5, 6, 7, 8, 9])
plt.savefig('./assets/rtp_evol.pdf')

plt.show()

bins = [-1, 0, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500]
labels = ['Loss'] + ['->{}x'.format(entry if entry < 1 else int(entry)) for entry in bins[2:]]

categorized = pd.cut(win_ratio, bins=bins, labels=labels).value_counts()

# convert to PMF
categorized = categorized / categorized.sum()
print(categorized)

_, ax = plt.subplots(1, 1, figsize=(12, 4))
ax.plot(np.arange(len(categorized)), categorized.values, 'bo', ms=6, mec='b')
ax.set_xticks(np.arange(len(categorized)))
ax.set_xticklabels(categorized.index)
ax.set_yscale('log')
ax.set_ylabel('Probability')
ax.set_xlabel('Win Category (multiples of wager)')
ax.set_title('Probability Distribution of Returns')
plt.savefig('./assets/rtp_dist.pdf')
plt.show()

print(f"The average RTP is {win_ratio.mean()}")