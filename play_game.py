from igt_session import IGTSlotSession
from helpers import get_url_from_name

# All game names are available in helpers.py
# We will watch the reels but disable the sound.
session = IGTSlotSession(get_url_from_name('siberian_storm'), headless=False, sound=False)
session.load_game()
session.spin(num_spins=None)  # run indefinitely until we close the window
session.save_results()
session.close()
