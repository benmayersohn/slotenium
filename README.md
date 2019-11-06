# Slotenium

This module allows one to automate playing demo (free play) versions of slot games using [Selenium](https://www.seleniumhq.org/). During each spin, the balance, wager, and winnings are recorded. Over many many spins, one can estimate the empirical probability distribution of the RTP, or "return to player". From this, one can calculate several metrics to compare the games and select one that suits a particular gambler's style.

A few notes:

* As of now, this works with certain online slot games by [International Game Technology (IGT)](https://www.igt.com/) and Aristocrat. The IGT games are drawn from official servers, while the Aristocrat games are taken from [supermegaslot.com](https://www.supermegaslot.com). Supermegaslot is known to host pirated games with potentially modified RTP values - making it a fun place to experiment with Slotenium!

* You **cannot** use this app to play with real money, and this is purely for educational purposes.

* If you use this app frequently, your IP address might get banned from the website that serves the games. I would therefore recommend using a [VPN](https://en.wikipedia.org/wiki/Virtual_private_network).

## How it Works

When you press the spin button on a slot game, the browser communicates with a server that runs a random number generator (RNG) to compute the result. This outcome is then sent back to the browser displayed on the reels. We can't gain access to the RNG because it is run server-side, but we can try to reconstruct the probability distribution of returns by running many simulations.

Nowadays most of these games are built in HTML5 - which is great for browser automation tools like Selenium. We can load one of these games and use Selenium to identify the spin buttons, along with the wager, winnings, and balance fields. The `IGTSlotSession` and `AristocratSlotSession` classes use Selenium to spin the reels and extract information about the outcome from the relevant fields. When we are done with a session, the outcomes are saved in a CSV file. Whether you play a game by IGT or Aristocrat, the output is stored in the same format and can be analyzed using the same code. We only include the analysis of a single IGT example in this repository (`siberian_storm_analysis.py`).


## Installation

To install the requirements for Slotenium, use

```bash
pip install -r requirements.txt
```

I recommend creating a virtual environment so that the proper versions of each package are installed without any conflicts.


## Directory Structure

Below is a breakdown of the files in this repository.
<pre class="language-bash"><code class="language-bash">slotenium
|____assets          
| |____rtp_dist.png                 # Probability distribution of RTP
| |____rtp_evol.png                 # Evolution of RTP with number of simulations
|____igt.py                         # Code for setting up IGT gambling session
|____aristocrat.py                  # Code for setting up Aristocrat gambling session
|____requirements.txt               # required libraries for running all code in this directory
|____results
| |____siberian_storm               # directory with output of simulations
|____README.md                      # this
|____siberian_storm_analysis.py     # for plotting output of simulations and calculating statistics of Siberian Storm
|____play_igt.py                    # run simulations of an IGT game (Siberian Storm by default)
|____play_aristocrat.py             # run simulations of an Aristocrat game (50 Dragons by default)
|____helpers.py                     # helper functions for running simulations and analysis.
</code></pre>

## Games

I have included a number of games by both companies in the file `helpers.py`, along with a function to construct the corresponding URL. All included games can be fully automated (meaning no user interaction is required to play indefinitely, even in bonus rounds).

You can use [this Google search](https://www.google.com/search?q="m.ac.rgsgames.com") to find more games that are compatible with Slotenium. Note that some of them require user interaction during bonus rounds, or to proceed through some initial instructions, and will time out if unattended.

## Example: Siberian Storm

From [VegasSlotsOnline](https://www.vegasslotsonline.com/igt/siberian-storm/):

> IGT's Siberian Storm is a tiger or feline themed slot machine with 5-reels and 720 paylines. The color theme of the slot machine is white, matching the theme of the Siberian Tiger and the snow-filled regions that it is found in. Symbols used in the game include the mighty Siberian tiger, an orange tiger, a gold-plated claw of the tiger, the eye of the tiger, an emerald ring and the Siberian Storm logo among others.

> The game has a wild symbol, one with the white tiger and also a scatter symbol, which triggers the bonus features. Siberian Storm is a slot that belongs to the family for Fire Horse slots and has **an impressive payout percentage of around 96%.**

So we know that the payout percentage is about 96%. We would like to confirm this via our simulations.

Using the `IGTSlotSession` tool, I recorded 11718 games of Siberian Storm. This is not nearly enough to capture the full distribution of returns, which would require infinitely many spins. But by the [law of large numbers](https://en.wikipedia.org/wiki/Law_of_large_numbers), the average RTP should converge to the true expected value.

Below I produced a probability distribution for the returns, binned into groups representing a range of multiples of the wager.

![PDF of RTP](./assets/rtp_dist.png)

The probability of losing is about 63.6%. This is comparable to the 20-line [Cleopatra slot machine](https://www.vegasslotsonline.com/igt/cleopatra/) (also by IGT), which lost 64.2% of the time over 10 million rounds of simulations (kudos to [Casino Guru](https://casino.guru/cleopatra-slot-math) for their analysis!)

### Average RTP

One can calculate an approximate average RTP for each game. Recall that for Siberian Storm, this was about 96%. I obtained 96.64% (see `siberian_storm_analysis.py`) - which is pretty close to the expected value! Below we can see how the average RTP evolves with the number of winnings.

![Evolution of RTP](./assets/rtp_evol.png)

### Volatility

Two games with the same average RTP can have very different probability distributions. One way to capture these differences is to break down the average RTP into a product of two measures: the **average RTP conditioned on winning** (RTPW); and the probability of winning. Low volatility games shift more weight onto the probability of winning, while high volatility games shift more weight onto the RTPW.

For Siberian Storm, the average RTPW is about **2.66 times the wager**. We arrive at this measure by dividing the average RTP as a fraction (0.9664) by the probability of winning (0.364). This is a medium volatility game, which is also true of 20-line Cleopatra. Compare this to 1-line Cleopatra, which has an RTP of 95.02% but only an [11.3% chance of a hit](https://casino.guru/cleopatra-slot-math). This corresponds to an RTPW of **8.4 times the wager** - a highly volatile game.

The RTPW is a useful measure but it is incomplete, as it does not describe the entire shape of the probability distribution. Another measure of volatility (and the more common one) is the **variance** of the return, or the average squared deviation of the observations from the mean. If we take the square root of the variance and divide it by the mean RTP, we get the **coefficient of variation** (CV), which is (in my opinion) the most useful measure of volatility.

If we run `siberian_storm_analysis.py`, we see that Siberian Storm has a CV of about 6.12. Using the probability distribution from Casino Guru, I get a CV for 20-line Cleopatra of about 5.58 - similar to that of Siberian Storm. 1-line Cleopatra has a much higher CV of 14.64.