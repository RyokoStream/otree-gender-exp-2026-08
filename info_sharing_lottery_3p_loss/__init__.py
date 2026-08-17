from otree.api import *
import random
import numpy as np

doc = """
3人グループ利得構造実験（Lossバージョン：前半 平均値ルール / 後半 メジアンルール）
"""


class C(BaseConstants):
    NAME_IN_URL = 'info_sharing_lottery_3p_loss'
    PLAYERS_PER_GROUP = 3
    NUM_ROUNDS = 4  # 全4ラウンド（1, 2: 平均値 / 3, 4: メジアン）
    INITIAL_ENDOWMENT = 2000  # 初期保有額 2000円


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    calculated_P = models.FloatField()  # グループ内で決定された確率 P


class Player(BasePlayer):
    # --- 1. 基本情報アンケート（Demographics用） ---
    student_id = models.StringField(
        label="IDを入力してください",
    )
    gender = models.StringField(
        label="あなたの戸籍上の性別を教えてください",
        choices=['男性', '女性'],
        widget=widgets.RadioSelect
    )
    age = models.IntegerField(
        label="あなたの年齢を入力してください（半角数字）",
        min=18, max=100
    )

    # --- 2. 練習画面の入力値 ---
    practice1_p = models.IntegerField(min=0, max=100, label="申告する確率 p_A (%)")
    practice2_p = models.IntegerField(min=0, max=100, label="申告する確率 p_B (%)")
    practice3_p = models.IntegerField(min=0, max=100, label="申告する確率 p_A (%)")
    practice4_p = models.IntegerField(min=0, max=100, label="申告する確率 p_B (%)")

    # --- 3. 本番意思決定の入力値 ---
    declaration = models.IntegerField(
        min=0, max=100,
        label="あなたにとって望ましい確率 p (%) を宣言してください"
    )

    # --- 4. 最終謝礼用の結果記録 ---
    selected_round = models.IntegerField()  # 支払対象として選ばれたラウンド
    final_p = models.FloatField()           # 選ばれたラウンドの集計確率 P
    chosen_state = models.IntegerField()    # 選ばれたラウンドで発生した状況（1 または 2）
    loss_amount = models.IntegerField()     # 選ばれたラウンドで発生した損失額（円）
    payoff_amount = models.IntegerField()   # 最終確定謝礼金（2000 - loss_amount）


# =========================================================
#  ページ定義
# =========================================================

class Demographics(Page):
    """実験開始前の基本情報入力画面"""
    form_model = 'player'
    form_fields = ['student_id', 'gender', 'age']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class Instructions(Page):
    """実験の全体説明画面"""
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


# --- 前半練習1・2（平均値ルール） ---

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
        your_p = player.practice1_p if player.practice1_p is not None else 0
        big_p = round((your_p + 30 + 50) / 300.0, 3)
        # 損失額の算出: 状況1は (1-P)*2000, 状況2は P*2000
        loss_s1 = int(round((1.0 - big_p) * C.INITIAL_ENDOWMENT))
        loss_s2 = int(round(big_p * C.INITIAL_ENDOWMENT))
        return {
            'your_p': your_p,
            'big_p': big_p,
            'loss_s1': loss_s1,
            'loss_s2': loss_s2,
            'payoff_s1': C.INITIAL_ENDOWMENT - loss_s1,
            'payoff_s2': C.INITIAL_ENDOWMENT - loss_s2,
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
        your_p = player.practice2_p if player.practice2_p is not None else 0
        big_p = round((70 + your_p + 50) / 300.0, 3)
        loss_s1 = int(round((1.0 - big_p) * C.INITIAL_ENDOWMENT))
        loss_s2 = int(round(big_p * C.INITIAL_ENDOWMENT))
        return {
            'your_p': your_p,
            'big_p': big_p,
            'loss_s1': loss_s1,
            'loss_s2': loss_s2,
            'payoff_s1': C.INITIAL_ENDOWMENT - loss_s1,
            'payoff_s2': C.INITIAL_ENDOWMENT - loss_s2,
        }


# --- 本番前の同期・グループ情報確認画面 ---

class GroupWaitPage(WaitPage):
    """第1ラウンド開始前のみ、全員が揃うのを待つページ"""
    title_text = "他のメンバーを待っています"
    body_text = "グループ全員が準備完了になるまでしばらくお待ちください..."

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class GroupInfo(Page):
    """グループ構成（性別）を表示する専用ページ（最初だけ表示）"""
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        r = player.round_number
        id_in_g = player.id_in_group
        role_map = {1: 'プレイヤーA', 2: 'プレイヤーB', 3: 'プレイヤーC'}

        group_info = []
        for p in player.group.get_players():
            try:
                p_r1 = p.in_round(1)
                gender_val = getattr(p_r1, 'gender', None)
            except Exception:
                gender_val = None

            group_info.append({
                'role_name': role_map.get(p.id_in_group, ''),
                'gender': gender_val if gender_val else '未回答',
                'is_me': (p.id_in_group == id_in_g)
            })

        return {
            'round_num': r,
            'group_info': group_info,
        }


# --- 本番意思決定画面 ---

class Decision(Page):
    form_model = 'player'
    form_fields = ['declaration']

    @staticmethod
    def vars_for_template(player: Player):
        r = player.round_number
        id_in_g = player.id_in_group

        if r in [1, 3]:
            prob_A, prob_B, prob_C = 80, 20, 50
        else:
            prob_A, prob_B, prob_C = 60, 40, 50

        probs = {1: prob_A, 2: prob_B, 3: prob_C}
        my_prob1 = probs.get(id_in_g, prob_A)

        role_map = {1: 'プレイヤーA', 2: 'プレイヤーB', 3: 'プレイヤーC'}

        return {
            'round_num': r,
            'role_name': role_map.get(id_in_g, 'プレイヤーA'),
            'prob_A': prob_A,
            'prob_B': prob_B,
            'prob_C': prob_C,
            'prob_A_rem': 100 - prob_A,
            'prob_B_rem': 100 - prob_B,
            'prob_C_rem': 100 - prob_C,
            'prob_result1': my_prob1,
            'prob_result2': 100 - my_prob1,
            # Lossバージョン表記用の数式文字列
            'payoff_result1_formula': '-(1 - P) × 2000円',
            'payoff_result2_formula': '-P × 2000円',
        }


class DecisionWaitPage(WaitPage):
    """毎ラウンドの意思決定後、全員の入力を待って確率 P を計算"""
    @staticmethod
    def after_all_players_arrive(group: Group):
        r = group.round_number
        players = group.get_players()
        declarations = [(p.declaration or 0) / 100.0 for p in players]

        if r <= 2:
            p_calc = sum(declarations) / 3.0
        else:
            p_calc = float(np.median(declarations))

        group.calculated_P = round(p_calc, 3)


# --- 後半練習3・4（メジアンルール） ---

class Practice3(Page):
    form_model = 'player'
    form_fields = ['practice3_p']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 2


class Practice3Results(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 2

    @staticmethod
    def vars_for_template(player: Player):
        your_p = player.practice3_p if player.practice3_p is not None else 0
        big_p = round(float(np.median([your_p / 100.0, 0.30, 0.50])), 3)
        loss_s1 = int(round((1.0 - big_p) * C.INITIAL_ENDOWMENT))
        loss_s2 = int(round(big_p * C.INITIAL_ENDOWMENT))
        return {
            'your_p': your_p,
            'big_p': big_p,
            'loss_s1': loss_s1,
            'loss_s2': loss_s2,
            'payoff_s1': C.INITIAL_ENDOWMENT - loss_s1,
            'payoff_s2': C.INITIAL_ENDOWMENT - loss_s2,
        }


class Practice4(Page):
    form_model = 'player'
    form_fields = ['practice4_p']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 2


class Practice4Results(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 2

    @staticmethod
    def vars_for_template(player: Player):
        your_p = player.practice4_p if player.practice4_p is not None else 0
        big_p = round(float(np.median([0.70, your_p / 100.0, 0.50])), 3)
        loss_s1 = int(round((1.0 - big_p) * C.INITIAL_ENDOWMENT))
        loss_s2 = int(round(big_p * C.INITIAL_ENDOWMENT))
        return {
            'your_p': your_p,
            'big_p': big_p,
            'loss_s1': loss_s1,
            'loss_s2': loss_s2,
            'payoff_s1': C.INITIAL_ENDOWMENT - loss_s1,
            'payoff_s2': C.INITIAL_ENDOWMENT - loss_s2,
        }


# --- 全ラウンド終了時の最終集計処理 ---

class FinalResultsWaitPage(WaitPage):
    """全ラウンド終了後、支払対象ラウンドを抽出して謝礼計算"""
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def after_all_players_arrive(group: Group):
        selected_r = random.randint(1, C.NUM_ROUNDS)

        for p in group.get_players():
            target_p = p.in_round(selected_r)
            target_g = group.in_round(selected_r)

            big_p = target_g.calculated_P if target_g.calculated_P is not None else 0.5
            id_in_g = target_p.id_in_group

            if selected_r in [1, 3]:
                prob1 = 80 if id_in_g == 1 else (20 if id_in_g == 2 else 50)
            else:
                prob1 = 60 if id_in_g == 1 else (40 if id_in_g == 2 else 50)

            drawn_state = 1 if random.random() < (prob1 / 100.0) else 2

            # Loss形式の計算: 状況1は (1-P)*2000の損失、状況2は P*2000の損失
            if drawn_state == 1:
                loss = int(round((1.0 - big_p) * C.INITIAL_ENDOWMENT))
            else:
                loss = int(round(big_p * C.INITIAL_ENDOWMENT))

            final_payoff = C.INITIAL_ENDOWMENT - loss

            final_p_obj = p.in_round(C.NUM_ROUNDS)
            final_p_obj.selected_round = selected_r
            final_p_obj.final_p = big_p
            final_p_obj.chosen_state = drawn_state
            final_p_obj.loss_amount = loss
            final_p_obj.payoff_amount = final_payoff
            final_p_obj.payoff = final_payoff


# --- 最終結果画面 ---

class FinalResults(Page):
    """全4ラウンドの入力履歴および確定謝礼金を表示"""
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        chosen_r = player.selected_round
        all_rounds_data = []

        for r in range(1, C.NUM_ROUNDS + 1):
            r_player = player.in_round(r)
            r_group = player.group.in_round(r)
            r_players = r_group.get_players()

            my_p = r_player.declaration or 0
            other_decls = [(p.declaration or 0) for p in r_players if p.id_in_group != r_player.id_in_group]

            id_in_g = r_player.id_in_group
            if r in [1, 3]:
                prob1 = 80 if id_in_g == 1 else (20 if id_in_g == 2 else 50)
            else:
                prob1 = 60 if id_in_g == 1 else (40 if id_in_g == 2 else 50)
            prob2 = 100 - prob1

            calc_p_round = r_group.calculated_P if r_group.calculated_P is not None else 0.5
            
            # 各状況での損失額
            loss_s1 = int(round((1.0 - calc_p_round) * C.INITIAL_ENDOWMENT))
            loss_s2 = int(round(calc_p_round * C.INITIAL_ENDOWMENT))

            if r == chosen_r:
                state = player.chosen_state
                round_loss = player.loss_amount
                round_pay = player.payoff_amount
            else:
                state = 1 if random.random() < (prob1 / 100.0) else 2
                round_loss = loss_s1 if state == 1 else loss_s2
                round_pay = C.INITIAL_ENDOWMENT - round_loss

            role_map = {1: 'プレイヤーA', 2: 'プレイヤーB', 3: 'プレイヤーC'}

            all_rounds_data.append({
                'round_num': r,
                'role_name': role_map.get(id_in_g, 'プレイヤーA'),
                'my_p': my_p,
                'other_p_1': other_decls[0] if len(other_decls) > 0 else 0,
                'other_p_2': other_decls[1] if len(other_decls) > 1 else 0,
                'group_P': calc_p_round,
                'prob_result1': prob1,
                'prob_result2': prob2,
                'loss_result1': loss_s1,
                'loss_result2': loss_s2,
                'drawn_result': state,
                'round_loss': round_loss,
                'round_payoff': round_pay,
            })

        return {
            'selected_round': chosen_r,
            'all_rounds': all_rounds_data,
            'final_loss': player.loss_amount,
            'final_payoff': player.payoff_amount,
        }


# =========================================================
#  ページ遷移順序
# =========================================================

page_sequence = [
    Demographics,
    Instructions,
    # --- 前半練習（平均値ルール） ---
    Practice1,
    Practice1Results,
    Practice2,
    Practice2Results,
    # --- 本番前の同期・グループ性別確認 ---
    GroupWaitPage,
    GroupInfo,
    Decision,
    DecisionWaitPage,
    # --- 後半練習（メジアンルール） ---
    Practice3,
    Practice3Results,
    Practice4,
    Practice4Results,
    # --- 最終結果集計 ---
    FinalResultsWaitPage,
    FinalResults,
]
