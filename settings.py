from os import environ

SESSION_CONFIGS = [
    # ▼ 今回作成した3人グループ実験（新規追加）
    dict(
        name='lottery_experiment_3p',
        display_name="3人グループ利得構造実験（前半平均・後半メジアン）",
        app_sequence=['lottery_experiment_3p'],
        num_demo_participants=3,  # 3人1グループのため
    ),
    # ▼ 以前作成されたアプリ
    dict(
        name='gender_lottery',
        display_name="情報共有型くじ実験",
        app_sequence=['gender_lottery'],
        num_demo_participants=2,
    ),
    # ▼ もとからあるサンプルアプリ一覧
    dict(
        name='guess_two_thirds',
        display_name="Guess 2/3 of the Average",
        app_sequence=['guess_two_thirds', 'payment_info'],
        num_demo_participants=3,
    ),
    dict(
        name='survey', 
        app_sequence=['survey', 'payment_info'], 
        num_demo_participants=1
    ),
    dict(
        name='mpl_demo',
        display_name='MPL (Holt–Laury) Demo',
        app_sequence=['mpl'],
        num_demo_participants=1,
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=1.00, participation_fee=0.00, doc=""
)

PARTICIPANT_FIELDS = []
SESSION_FIELDS = []

# ISO-639 code (日本語化)
LANGUAGE_CODE = 'ja'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'JPY'
USE_POINTS = True

ROOMS = [
    dict(
        name='econ101',
        display_name='Econ 101 class',
        participant_label_file='_rooms/econ101.txt',
    ),
    dict(name='live_demo', display_name='Room for live demo (no participant labels)'),
]

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """
Here are some oTree games.
"""

SECRET_KEY = '9147097385685'

INSTALLED_APPS = ['otree']
