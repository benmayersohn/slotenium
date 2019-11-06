from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import requests
from requests.exceptions import RequestException
from typing import Optional
import selenium.common.exceptions as slex
from datetime import datetime
import csv


# Check to see if game action belongs to passed tuple of options
# actions include: "spin", "normal", "spin_OR_gamble", or "winLines"
class ActionBelongsTo(object):
    def __init__(self, values: tuple):
        self.values = values

    def __call__(self, driver):
        return driver.execute_script("return game.action;") in self.values


# Only return true once reels are visible...
class PageLoaded(object):
    def __call__(self, driver):
        position = driver.execute_script("return reels['position'][0];")
        try:
            float(position['height'])
        except (ValueError, TypeError):
            return False
        else:
            return True


class AristocratSlotSession:
    """
    This class allows us to set up a session on an Aristocrat slot machine, play the game, and store the results.
    The outcomes can be saved in a CSV file. Each row contains:

    Time: time at which reels were spun (or balance was replenished)
    Wager: Wager placed. As of now we do not have the option to change this.
    Win: Amount won on spin
    Balance: Balance post-win
    """

    # Header for saving files to CSV
    CSV_HEADER = ('Time', 'Wager', 'Win', 'Balance')

    def __init__(self, url, headless: bool = True, sound: bool = False):

        self.url = url

        # List of tuples; each tuple is the outcome of a spin
        self.outcomes = list()

        # Is sound enabled?
        self.sound = sound

        options = webdriver.ChromeOptions()

        if headless:
            options.add_argument('headless')

        self.driver = webdriver.Chrome(options=options)

    def exception_quit(self, e: Exception, err_message: str = None):
        """
        Helper function for closing the driver, saving results, and raising an exception.
        """
        self.driver.quit()

        if len(self.outcomes) > 0:
            self.save_results()

        if err_message is None:
            raise e
        else:
            raise Exception(err_message) from e

    def get_wager(self):
        cmd = "return game.getCash(game.config['betInfo']['totalBet']);"
        return float(self.driver.execute_script(cmd))

    def get_balance(self):
        cmd = "return game.getCash(game.config['balance']);"
        return float(self.driver.execute_script(cmd))

    def get_win(self):
        cmd = "return game.getCash(game.config['win']);"
        return float(self.driver.execute_script(cmd))

    def get_true_url(self):
        # use Beautiful Soup to fetch page source
        try:
            r = requests.get(self.url).text
            soup = BeautifulSoup(r, 'lxml')
        except RequestException as e:
            raise Exception("Could not connect, soup not downloaded...") from e

        # get iFrame source
        return soup.find('iframe')['src']

    def load_game(self):
        # load game
        self.driver.get(self.get_true_url())

        # Wait until page loaded
        try:
            WebDriverWait(self.driver, 100).until(PageLoaded())
            WebDriverWait(self.driver, 100).until(ActionBelongsTo(('normal',)))
        except slex.TimeoutException as e:
            self.exception_quit(e, "Game not showing up! WebDriver closed.")

        # disable sound
        if not self.sound:
            # opens sound menu, disables sound, then closes menu and goes back to game
            cmd = "game['settingStandard'](); game['settingStandardSound'](); game['settingStandard']();"
            self.driver.execute_script(cmd)

        # create initial row
        # (time, wager, win, balance)
        self.outcomes.append((str(datetime.now()), 0.0, 0.0, self.get_balance()))

    def spin_cycle(self):
        # Hit spin command, wait until we're spinning, and then wait until we stop spinning
        self.driver.execute_script("game.actionSpin();")
        WebDriverWait(self.driver, 1000).until(ActionBelongsTo(('spin',)))
        WebDriverWait(self.driver, 1000).until(ActionBelongsTo(('normal', 'spin_OR_gamble')))

    def spin_once(self, restore_balance: bool = True) -> tuple:

        # Check our balance. If it is too low, either (1) refresh the page or (2) print a message...
        if self.get_wager() > self.get_balance():
            if restore_balance:
                print("We need to refresh the page and restore your balance...")
                self.load_game()
            else:
                self.exception_quit(ValueError("Your balance is too low! Set restore_balance=True"))

        # record time of spin
        spin_time = str(datetime.now())

        while True:
            # spin once
            self.spin_cycle()

            # stop there if we don't have free spins
            if not bool(self.driver.execute_script("return game.config.freeSpin;")):
                break

        # Now record wins
        balance = self.get_balance()
        wager = self.get_wager()
        win = self.get_win()

        # store result
        result = (spin_time, wager, win, balance)
        self.outcomes.append(result)
        return result

    def spin(self, num_spins: Optional[int] = 1, restore_balance: bool = True):

        # Should we spin or not?
        def spin_condition_true(spin_number):
            return True if num_spins is None else spin_number < num_spins

        try:
            # stop spinning when we close the window...
            count = 0
            while spin_condition_true(count):
                count += 1
                result = self.spin_once(restore_balance=restore_balance)
                print(f"Spin {count}: Wager={result[1]}, Win={result[2]}, Balance={result[3]}")

        except (slex.NoSuchWindowException, KeyboardInterrupt):  # need to use KeyboardInterrupt if headless...
            print("\nSession terminated by user.")
        except slex.TimeoutException as e:
            self.exception_quit(e, "\nSession timed out!")
        except slex.WebDriverException as e:
            self.exception_quit(e, "\nSome exception occurred!")

    # Store results in CSV file
    def save_results(self, to: str = 'slot_results.csv', header: bool = True):
        try:
            with open(to, 'w') as f:
                writer = csv.writer(f, quotechar='"', quoting=csv.QUOTE_NONNUMERIC)  # quote the date...

                if header:
                    writer.writerow(self.CSV_HEADER)

                for result in self.outcomes:
                    writer.writerow(result)
        except IOError:
            print("There was a problem writing to the file!")

    def close(self):
        self.driver.quit()
