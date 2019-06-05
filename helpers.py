"""
helpers.py: helper functions for IGT slot player
"""

from urllib.parse import urlunparse, urlencode

# Identifiers for IGT games
# Software ID: Unique ID for the game
# Skin Code: Serves up the game's graphics.
# NS Code: Code for the eBetting client (GNUG = Golden Nugget, AMYA = Amaya)
softwareid = {'wolf_run': '200-1196-012', 'lil_lady': '200-1190-011', 'siberian_storm': '200-1150-003',
              'davinci_diamonds': '200-1100-011', 'cleopatra': '200-1173-001', 'double_diamond': '200-1219-001',
              'triple_diamond': '200-1221-001', 'red_hot': '200-1303-002'}

skincode = {'wolf_run': 'CSRS', 'lil_lady': 'GNT1',
            'siberian_storm': 'GNT2', 'davinci_diamonds': 'GNT2', 'cleopatra': 'GNT2', 'double_diamond': 'GNT2',
            'triple_diamond': 'GNT2', 'red_hot': 'CSR1'}

nscode = {'wolf_run': 'AMYA', 'lil_lady': 'GNUG',
          'siberian_storm': 'GNUG', 'davinci_diamonds': 'GNUG', 'cleopatra': 'GNUG', 'double_diamond': 'GNUG',
          'triple_diamond': 'GNUG', 'red_hot': 'AMYA'}


def get_url_from_name(name):
    """
    Use the name of the game (keys in the dictionaries above) to construct a valid URL
    """
    scheme = 'https'
    netloc = 'm.ac.rgsgames.com'  # RGS = "remote game server" by IGT
    path = '/games/index.html'
    params = ''

    query = dict()
    query['currencycode'] = 'FPY'  # "Free PlaY"
    query['securetoken'] = '999999'  # Can be anything
    query['countrycode'] = 'CA'  # Canada
    query['language'] = 'en'  # Only English supported right now (sorry!)
    query['softwareid'] = softwareid[name]
    query['skincode'] = skincode[name]
    query['nscode'] = nscode[name]

    # link query arguments
    query_str = urlencode([pair for pair in query.items()])

    fragment = ''
    return urlunparse((scheme, netloc, path, params, query_str, fragment))

