from otree.api import *
import random
import numpy as np

doc = """
3人グループによる期待値申告実験
前半：平均値ルール (練習2回 + 本番2回)
後半：メジアンルール (練習2回 + 本番2回)
"""

class C(BaseConstants):
    NAME_IN_URL = 'lottery_experiment_3p'
    PLAYERS_PER_GROUP = 3
    NUM_ROUNDS = 4  # 本番のラウンド数（第1, 2: 平均 / 第3, 4: メジアン）

    # 練習用の固定数値
    PRACTICE_A_P1 = 0.7
    PRACTICE_B_P1 = 0.3
    PRACTICE_C_P1 = 0.5


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # 本番用の入力値
    declaration = models.IntegerField(
        min=0, max=100,
        label="あなたにとって望ましい p の値（0 〜 100）を入力してください"
    )
    
    # 練習用の入力値
    practice1_p = models.IntegerField(min=0, max=100)
    practice2_p = models.IntegerField(min=0, max=100)
    practice3_p = models.IntegerField(min=0, max=100)
    practice4_p = models.IntegerField(min=0, max=100)

    # 最終結果用フィールド（Player単位で保持）
    selected_round = models.IntegerField()
    chosen_state = models.IntegerField()
    final_p = models.FloatField()
    payoff_amount = models.IntegerField()


# ---------------------------------------------------------------
# ページクラスの定義
# ---------------------------------------------------------------

class Instructions(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


# --- 前半（平均値ルール）練習 ---
class Practice1(Page):
    form_model = 'player'
    form_fields = ['practice1_p']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class Practice1Results(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        # A(入力値), B(30), C(50) の平均
        p_a = player.practice1_p / 100.0
        p_b = 0.30
        p_c = 0.50
        big_p = (p_a + p_b + p_c) / 3.0
        payoff_s1 = int(big_p * 2000)
        payoff_s2 = int((1 - big_p) * 2000)
        return {
            'your_p': player.practice1_p,
            'big_p': round(big_p, 3),
            'payoff_s1': payoff_s1,
            'payoff_s2': payoff_s2,
        }


class Practice2(Page):
    form_model = 'player'
    form_fields = ['practice2_p']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class Practice2Results(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        # A(70), B(入力値), C(50) の平均
        p_a = 0.70
        p_b = player.practice2_p / 100.0
        p_c = 0.50
        big_p = (p_a + p_b + p_c) / 3.0
        payoff_s1 = int(big_p * 2000)
        payoff_s2 = int((1 - big_p) * 2000)
        return {
            'your_p': player.practice2_p,
            'big_p': round(big_p, 3),
            'payoff_s1': payoff_s1,
            'payoff_s2': payoff_s2,
        }


# --- 本番ラウンド (Decision) ---
class Decision(Page):
    form_model = 'player'
    form_fields = ['declaration']

    @staticmethod
    def vars_for_template(player: Player):
        r = player.round_number
        is_median = (r >= 3)
        
        # セッション1 (1, 3ラウンド) と セッション2 (2, 4ラウンド) の確率割り当て
        if r in [1, 3]:
            p_a1, p_a2 = 80, 20
            p_c1, p_c2 = 50, 50
            p_b1, p_b2 = 20, 80
        else:
            p_a1, p_a2 = 60, 40
            p_c1, p_c2 = 50, 50
            p_b1, p_b2 = 40, 60

        # プレイヤーのID（1,2,3）に応じた役割名
        role_map = {1: 'プレイヤーA', 2: 'プレイヤーC', 3: 'プレイヤーB'}
        role_name = role_map.get(player.id_in_group, 'プレイヤーA')

        return {
            'round_num': r,
            'is_median': is_median,
            'role_name': role_name,
            'prob_a_1': p_a1, 'prob_a_2': p_a2,
            'prob_c_1': p_c1, 'prob_c_2': p_c2,
            'prob_b_1': p_b1, 'prob_b_2': p_b2,
        }


class DecisionWaitPage(WaitPage):
    body_text = "他のプレイヤーの入力完了を待っています..."


# --- 後半（メジアンルール）練習 ---
class Practice3(Page):
    form_model = 'player'
    form_fields = ['practice3_p']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 3  # 後半本番の直前に挿入


class Practice3Results(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 3

    @staticmethod
    def vars_for_template(player: Player):
        # A(入力値), B(30), C(50) のメジアン
        p_a = player.practice3_p / 100.0
        p_b = 0.30
        p_c = 0.50
        big_p = float(np.median([p_a, p_b, p_c]))
        payoff_s1 = int(big_p * 2000)
        payoff_s2 = int((1 - big_p) * 2000)
        return {
            'your_p': player.practice3_p,
            'big_p': round(big_p, 3),
            'payoff_s1': payoff_s1,
            'payoff_s2': payoff_s2,
        }


class Practice4(Page):
    form_model = 'player'
    form_fields = ['practice4_p']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 3


class Practice4Results(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 3

    @staticmethod
    def vars_for_template(player: Player):
        # A(70), B(入力値), C(50) のメジアン
        p_a = 0.70
        p_b = player.practice4_p / 100.0
        p_c = 0.50
        big_p = float(np.median([p_a, p_b, p_c]))
        payoff_s1 = int(big_p * 2000)
        payoff_s2 = int((1 - big_p) * 2000)
        return {
            'your_p': player.practice4_p,
            'big_p': round(big_p, 3),
            'payoff_s1': payoff_s1,
            'payoff_s2': payoff_s2,
        }


# --- 全ラウンド終了後の最終計算 WaitPage ---
class FinalResultsWaitPage(WaitPage):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def after_all_players_arrive(group: Group):
        # 全4ラウンドの中から1つのラウンドをランダム選出
        chosen_r = random.randint(1, C.NUM_ROUNDS)
        
        for p in group.get_players():
            target_player = p.in_round(chosen_r)
            target_group = target_player.group
            players_in_rg = target_group.get_players()
            
            # 各プレイヤーの宣言値を取得
            decls = [pl.declaration / 100.0 for pl in players_in_rg]
            
            # 平均かメジアンの計算
            if chosen_r <= 2:
                calc_p = sum(decls) / 3.0
            else:
                calc_p = float(np.median(decls))
            
            # 決定ラウンドの自身の役割と状況1の確率の判定
            id_in_g = target_player.id_in_group
            if chosen_r in [1, 3]:  # セッション1
                prob_s1 = 0.8 if id_in_g == 1 else (0.5 if id_in_g == 2 else 0.2)
            else:                  # セッション2
                prob_s1 = 0.6 if id_in_g == 1 else (0.5 if id_in_g == 2 else 0.4)
            
            # 状況1か状況2の抽選
            state = 1 if random.random() < prob_s1 else 2
            
            # 得点計算
            if state == 1:
                payoff = int(calc_p * 2000)
            else:
                payoff = int((1 - calc_p) * 2000)
            
            # 最終ラウンド(第4ラウンド)のPlayerオブジェクトに保存
            p.selected_round = chosen_r
            p.chosen_state = state
            p.final_p = round(calc_p, 3)
            p.payoff_amount = payoff
            p.payoff = payoff  # oTree標準のpayoffにも代入


class Results(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS


# ---------------------------------------------------------------
# ページ遷移順序の設定
# ---------------------------------------------------------------
page_sequence = [
    Instructions,
    # 前半練習
    Practice1,
    Practice1Results,
    Practice2,
    Practice2Results,
    # 前半本番 (ラウンド 1, 2)
    Decision,
    DecisionWaitPage,
    # 後半練習 (ラウンド 3の開始時に実行)
    Practice3,
    Practice3Results,
    Practice4,
    Practice4Results,
    # 後半本番 (ラウンド 3, 4)
    # ※ラウンド3・4ではDecisionが再度実行されます
    FinalResultsWaitPage,
    Results,
]
