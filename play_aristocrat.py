from aristocrat import AristocratSlotSession
from helpers import get_url_from_name

# All game names are available in helpers.py
# We will watch the reels but disable the sound.
session = AristocratSlotSession(get_url_from_name('50_dragons', brand='aristocrat'), headless=False)
session.load_game()
session.spin(num_spins=None)  # run indefinitely until we close the window
session.save_results()
session.close()
