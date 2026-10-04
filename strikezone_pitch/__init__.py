import json
from otree.api import *

doc = """
ストライクゾーン配球ゲーム（野球配球シミュレーション）

プレイヤーは架空のバッターに対して10球の観察（練習）ラウンドを行い、
バッターの弱点ゾーンを推測する。その後、本番ラウンドで「適切と思うゾーン」を回答し、
キャッチャーの主張（ゾーン0）を踏まえて実際にキャッチャーへ伝えるサイン q を決定する。
実際の投球ゾーンは q / 2 となり、三振なら 2000 × (1 + q) / 2、
ホームランなら 2000 × (1 - q) / 2 の報酬が得られる、チープトーク型の意思決定ゲーム。
"""


class C(BaseConstants):
    NAME_IN_URL = 'strikezone_pitch'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    NUM_PRACTICE_PITCHES = 10
    # バッターの弱点ゾーン（観察ラウンドでプレイヤーが探る対象）
    BATTER_WEAK_ZONE = 0.35
    # 弱点ゾーンとの差がこの範囲以内なら三振
    STRIKE_THRESHOLD = 0.20
    # キャッチャーが主張するゾーン
    CATCHER_ZONE = 0.0
    # 報酬計算のベース額（円）
    REWARD_BASE = 2000


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # 観察ラウンド10球分の履歴（JSON文字列。[{count, zone, result, isStrike}, ...]）
    practice_data = models.LongStringField(blank=True)

    ideal_zone = models.FloatField(
        label="あなたはどのゾーンが適切だと思いますか？ (0.00 〜 1.00):",
        min=0.0,
        max=1.0,
    )
    sign_q = models.FloatField(
        label="そのうえで、あなたはキャッチャーにどのゾーン（サイン q）が適切であると伝えますか？ (0.00 〜 1.00):",
        min=0.0,
        max=1.0,
    )

    actual_zone = models.FloatField(blank=True)
    is_strike = models.BooleanField(blank=True)
    reward = models.IntegerField(blank=True)


def get_is_strike(zone: float) -> bool:
    return abs(zone - C.BATTER_WEAK_ZONE) <= C.STRIKE_THRESHOLD


# --- PAGES ---

class Introduction(Page):
    pass


class Practice(Page):
    form_model = 'player'
    form_fields = ['practice_data']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            max_practice=C.NUM_PRACTICE_PITCHES,
            batter_weak_zone=C.BATTER_WEAK_ZONE,
            strike_threshold=C.STRIKE_THRESHOLD,
        )

    @staticmethod
    def error_message(player: Player, values):
        raw = values.get('practice_data', '')
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            return "観察データが正しく記録されていません。最初からやり直してください。"
        if not isinstance(data, list) or len(data) != C.NUM_PRACTICE_PITCHES:
            return f"{C.NUM_PRACTICE_PITCHES}回すべて投球してから進んでください。"


class Transition(Page):
    pass


class FinalStep1(Page):
    form_model = 'player'
    form_fields = ['ideal_zone']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(history=json.loads(player.practice_data))


class FinalStep2(Page):
    form_model = 'player'
    form_fields = ['sign_q']

    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            history=json.loads(player.practice_data),
            catcher_zone=C.CATCHER_ZONE,
            reward_base=C.REWARD_BASE,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        q = player.sign_q
        actual_zone = (C.CATCHER_ZONE + q) / 2
        is_strike = get_is_strike(actual_zone)

        player.actual_zone = round(actual_zone, 4)
        player.is_strike = is_strike

        if is_strike:
            reward = round(C.REWARD_BASE * (1 + q) / 2)
        else:
            reward = round(C.REWARD_BASE * (1 - q) / 2)

        player.reward = reward
        player.payoff = reward


class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return dict(
            ideal_zone=player.ideal_zone,
            sign_q=player.sign_q,
            actual_zone=player.actual_zone,
            is_strike=player.is_strike,
            reward=player.reward,
        )


page_sequence = [
    Introduction,
    Practice,
    Transition,
    FinalStep1,
    FinalStep2,
    Results,
]
