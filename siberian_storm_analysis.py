import pandas as pd
from os import listdir
from os.path import isfile, join
import matplotlib.pyplot as plt 
import numpy as np

plotting_on = True

filedir = './results/siberian_storm/'
filenames = [filedir + f for f in listdir(filedir) if isfile(join(filedir, f))]

# Import
df = pd.concat((pd.read_csv(f) for f in filenames), axis=0, sort=False)
df = df.sort_values(by=['Time'])

# Compute win as a fraction of wager
df = df[df['Wager'] > 0]
win_ratio = df['Win'] / df['Wager']

print(f"We have {len(win_ratio)} observations.\n")

# Divide winnings into categories (see rtp_dist.png)
bins = [-1, 0, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500]
labels = ['Loss'] + ['->{}x'.format(entry if entry < 1 else int(entry)) for entry in bins[2:]]

categorized = pd.cut(win_ratio, bins=bins, labels=labels).value_counts().reindex(labels)

# convert to PMF
categorized = categorized / categorized.sum()

print(f"Siberian Storm has an average RTP of {win_ratio.mean()}")
print(f"Siberian Storm has a win probability of {1-categorized['Loss']}")
print(f"Siberian Storm has an average RTPW of {win_ratio.mean() / (1 - categorized['Loss'])}")

variance = win_ratio.var()
cv = np.sqrt(variance)/win_ratio.mean()
print(f"Siberian Storm has a CV of {cv}\n")

# Compare with 20-line Cleopatra and 1-line Cleopatra
# See https://casino.guru/cleopatra-slot-math for probabilities and intervals
# We scale by a constant to achieve the desired payout

# 20-line
intervals = np.array([
                [0., 0.2],
                [0.2, 0.5],
                [0.5, 1.],
                [1., 2.],
                [2., 5.],
                [5., 10.],
                [10., 20.],
                [20., 50.],
                [50., 100.],
                [100., 200.],
                [200., 500.],
                [500., 1000.]
            ])

vals = np.array([0.] + [float(np.mean(x)) for x in intervals[1:]])

# Payout is 95.025% with this scaling coefficient
probabilities = 0.7987446566693283 * np.array(
[929482, 740452, 563289, 1031867, 149001, 92050, 58006, 17450, 3538, 505, 20]
) / 10000000.
probabilities = np.array([1-probabilities.sum()] + probabilities.tolist())

rtp_20 = np.sum(vals * probabilities)
var_20 = np.sum((vals-rtp_20)**2 * probabilities)

print(f'We gave 20-line Cleopatra an RTP of {rtp_20}')
print(f'20-line Cleopatra has a win probability of {1-probabilities[0]}')
print(f'20-line Cleopatra has an RTPW of {rtp_20 / (1-probabilities[0])}')
print(f'20-line Cleopatra has a CV of {np.sqrt(var_20) / rtp_20}\n')

# 1-line
intervals = np.array([
                [0., 2.],
                [2., 5.],
                [5., 10.],
                [10., 20.],
                [20., 50.],
                [50., 100.],
                [100., 200.],
                [200., 500.],
                [500., 1000.],
                [1000., 2000.],
                [2000., 5000.],
                [5000., 10000.],
                [10000., 20000.]
            ])

vals = np.array([0.] + [float(np.mean(x)) for x in intervals[1:]])

# Payout is 95.025% with this scaling coefficient
probabilities = 0.7233308569575265 * np.array(
            [8761210, 628815, 1008567, 544354, 273149, 82322, 52222, 8952, 1532, 411, 21, 6]
            ) / 100000000.
probabilities = np.array([1-probabilities.sum()] + probabilities.tolist())

rtp_1 = np.sum(vals * probabilities)
var_1 = np.sum((vals-rtp_20)**2 * probabilities)

print(f'We gave 1-line Cleopatra an RTP of {rtp_1}')
print(f'1-line Cleopatra has a win probability of {1-probabilities[0]}')
print(f'1-line Cleopatra has an RTPW of {rtp_1 / (1-probabilities[0])}')
print(f'1-line Cleopatra has a CV of {np.sqrt(var_1) / rtp_1}')

##############################################################################

# Plots

if plotting_on:
    # plot RTP evolution with number of simulations
    _, ax = plt.subplots(1, 1)
    means = win_ratio.expanding().mean()
    ax.plot(np.arange(len(means)), means)
    ax.set_title('RTP Evolution')
    ax.set_xlabel('Simulation Number')
    ax.set_ylabel('Mean RTP (multiple of wager)')
    ax.set_yticks([1, 2, 3, 4, 5, 6, 7, 8, 9])
    plt.savefig('./assets/rtp_evol.png')
    plt.show()

    _, ax = plt.subplots(1, 1, figsize=(12, 4))
    ax.plot(np.arange(len(categorized)), categorized.values, 'bo', ms=6, mec='b')
    ax.set_xticks(np.arange(len(categorized)))
    ax.set_xticklabels(categorized.index)
    ax.set_yscale('log')
    ax.set_ylabel('Probability')
    ax.set_xlabel('Win Category (multiples of wager)')
    ax.set_title('Probability Distribution of Returns')
    plt.savefig('./assets/rtp_dist.png')
    plt.show()
