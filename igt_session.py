from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from typing import List, Optional
import selenium.common.exceptions as slex
from selenium.webdriver.remote.webelement import WebElement
from datetime import datetime
import csv


# Class that checks whether or a button has been made invisible. We use this on the regular spin button.
# That's how we know we've started spinning...
class ButtonInvisible(object):
    def __init__(self, element: WebElement):
        self.element = element

    def __call__(self, driver):
        try:
            return not self.element.is_displayed()
        except slex.StaleElementReferenceException:
            return False


# Checks to see if the outcome of the spin has been determined.
# Either:
# 1) spin_element appears (normal spin result, or we finished a bonus)
# 2) We hit a bonus (start_bonus_element appears)
# 3) We ran out of funds. (insufficient_funds appears)
class SpinOutcomeDetermined(object):

    # If this is found, we're displaying a dialog that we're out of money
    insufficient_xpath_visible = ("//div[text()='Insufficient funds to spin.']"
                                  "/ancestor::div[contains(@style,'visibility: inherit')]")

    def __init__(self, spin_element: WebElement, other_elements: List[WebElement]):

        self.spin_element = spin_element
        self.other_elements = other_elements

    def __call__(self, driver: webdriver):
        try:
            
            # Return true if our original spin button is back
            if self.spin_element.is_displayed():
                return True

            # If a different button is visible, click it.
            for element in self.other_elements:
                try:
                    if element.is_displayed():
                        element.click()
                        break
                except (slex.ElementNotVisibleException, slex.WebDriverException):
                    self.other_elements.remove(element)

            # Some games explicitly pass an "Insufficient funds" dialog.
            # Return True if this happens...
            try:
                driver.find_element_by_xpath(self.insufficient_xpath_visible)
                return True
            except slex.NoSuchElementException:
                pass
            
        except slex.StaleElementReferenceException:
            return False


class IGTSlotSession:
    """
    This class allows us to set up a session on an IGT slot machine, play the game, and store the results.
    The outcomes can be saved in a CSV file. Each row contains:

    Time: time at which reels were spun (or balance was replenished)
    Wager: Wager placed. As of now we do not have the option to change this.
    Win: Amount won on spin
    Balance: Balance post-win

    As of 6/3/2019, the wager is fixed at the default value EXCEPT when the page is (re-)loaded. Then the
    starting balance is listed, along with a wager and win of 0. 
    """

    # Header for saving files to CSV
    CSV_HEADER = ('Time', 'Wager', 'Win', 'Balance')

    def __init__(self, url, headless: bool = True, sound: bool = False):

        self.url = url

        # These elements display the wager ('total bet'), balance, and win. These will be Selenium WebElement objects
        self.wager_element = None
        self.balance_element = None
        self.win_element = None

        # Button for regular spin. This will be a div element.
        self.spin_button = None

        # Other buttons on same level (hidden when spin button is visible)
        # 1) fast-forward button through a big win
        # 2) "start bonus" button
        self.other_buttons = None

        # List of tuples; each tuple is the outcome of a spin
        self.outcomes = list()

        # Is sound enabled?
        self.sound = sound

        options = webdriver.ChromeOptions()

        # Set user agent to a SAMSUNG device so full screen is not opened...
        # Only applies when headless=False
        # Source: https://deviceatlas.com/blog/samsung-phones-user-agent-strings-list
        ua = ("Mozilla/5.0 (Linux; Android 7.0; SAMSUNG SM-G610M Build/NRD90M) "
              "AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/7.4 "
              "Chrome/59.0.3071.125 Mobile Safari/537.36")

        if headless:
            options.add_argument('headless')
        else:
            options.add_argument(f"user-agent={ua}")

        self.driver = webdriver.Chrome(options=options)

        self.just_loaded = None

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

    @staticmethod
    def value_from_element(sel_element: WebElement):
        return None if sel_element is None else sel_element.get_attribute('innerHTML')

    def get_wager(self):
        return float(self.value_from_element(self.wager_element))

    def get_balance(self):
        return float(self.value_from_element(self.balance_element))

    def get_win(self):
        return float(self.value_from_element(self.win_element))

    # We will check for labels in a case-insensitive manner
    @staticmethod
    def match_lowercase_xpath(text: str):
        return f"translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='{text.lower()}'"

    # Get value from adjacent label (e.g. "Balance" => fetch span whose inner text says "balance" [case-insensitive])
    def element_from_adj_label(self, text: str):
        return self.driver.find_element_by_xpath(
            f"//span[{self.match_lowercase_xpath(text)}]/preceding-sibling::span")

    def load_game(self):
        self.driver.get(self.url)

        # This dialog appears before every game. It asks if we want the sound on or off...
        sound_selector = "//div[text()='Would you like sound?']"  # XPATH

        try:
            WebDriverWait(self.driver, 20).until(EC.visibility_of_element_located((By.XPATH, sound_selector)))
            sound_span = self.driver.find_element_by_xpath(f"//div[text()='{'Yes' if self.sound else 'No'}']")

            # Click the button in which the "Yes"/"No" span is stored and click the right button.
            sound_span.find_element_by_xpath("./..").click()
        except slex.TimeoutException as e:
            self.exception_quit(e, "Loader not showing up! Webdriver closed.")

        # Wait until next page loaded
        try:
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, f"//span[{self.match_lowercase_xpath('total bet')}]")))
        except slex.TimeoutException as e:
            self.exception_quit(e, "Can't find expected 'TOTAL BET' text on next page...WebDriver closed.")
    
        # Extract wager, balance, win
        self.wager_element = self.element_from_adj_label('total bet')
        self.balance_element = self.element_from_adj_label('balance')
        self.win_element = self.element_from_adj_label('win')

        # first element within game div such that style contains 'visibility: inherit;'. This is the spin button
        spin_xpath = "//div[@id='game']//div[contains(@style,'visibility: inherit')]"
        self.spin_button = self.driver.find_element_by_xpath(spin_xpath)

        # Next, we get all other buttons on the same level as the spin button
        # These include the "fast-forward" button through big wins, and the start bonus button.
        self.other_buttons = list()

        # get all preceding elements
        try:
            prev_xpath = spin_xpath
            while True:
                prev_xpath += "/preceding-sibling::div"
                self.other_buttons.append(self.driver.find_element_by_xpath(prev_xpath))
        except slex.NoSuchElementException:
            pass

        # get all following elements
        try:
            next_xpath = spin_xpath
            while True:
                next_xpath += "/following-sibling::div"
                self.other_buttons.append(self.driver.find_element_by_xpath(next_xpath))
        except slex.NoSuchElementException:
            pass

        # create initial row
        # (time, wager, win, balance)
        self.outcomes.append((str(datetime.now()), 0.0, 0.0, self.get_balance()))

        self.just_loaded = True

    def spin_once(self, restore_balance: bool = True) -> tuple:

        # Check our balance. If it is too low, either (1) refresh the page or (2) print a message...
        if self.get_wager() > self.get_balance():
            if restore_balance:
                print("We need to refresh the page and restore your balance...")
                self.load_game()
            else:
                self.exception_quit(ValueError("Your balance is too low! Set restore_balance=True"))

        old_balance = self.get_balance()

        if self.just_loaded and not self.spin_button.is_displayed():
            self.just_loaded = False
        else:
            self.spin_button.click()

        # record time of spin
        spin_time = str(datetime.now())

        try:
            # First, make sure spin button becomes invisible
            WebDriverWait(self.driver, 1000).until(ButtonInvisible(self.spin_button))

            # Now - make sure spin button reappears OR we get a dialog about running out of money...
            WebDriverWait(self.driver, 1000).until(SpinOutcomeDetermined(self.spin_button, self.other_buttons))
        except slex.TimeoutException as e:
            self.exception_quit(e, "Lost connection! WebDriver closed.")

        # Check to see if we won anything
        balance = self.get_balance()
        wager = self.get_wager()

        # Get win (if we have any)
        try:
            win = self.get_win()

            # make sure the math works out...sometimes container is hidden but old winnings are left there
            if old_balance - wager + win != balance:
                win = 0.
                
        except ValueError:  # if field is filled with whitespace, for example...
            win = 0.

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
            print("\nSession timed out!")

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
