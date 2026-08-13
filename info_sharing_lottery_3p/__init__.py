from otree.api import *
import random
import numpy as np

doc = """
3人グループ利得構造実験（前半：平均値ルール / 後半：メジアンルール）
"""


class C(BaseConstants):
    NAME_IN_URL = 'lottery_experiment_3p'
    PLAYERS_PER_GROUP = 3
    NUM_ROUNDS = 4  # 全4ラウンド（1, 2: 平均値 / 3, 4: メジアン）


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    calculated_P = models.FloatField()  # グループ内で決定された確率 P


class Player(BasePlayer):
    # --- 1. 基本情報アンケート（Demographics用） ---
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

    # --- 4. 最終謝礼用の結果記録（第4ラウンドのPlayerオブジェクトに保存） ---
    selected_round = models.IntegerField()  # 支払対象として選ばれたラウンド
    final_p = models.FloatField()          # 選ばれたラウンドの集計確率 P
    chosen_state = models.IntegerField()     # 選ばれたラウンドで発生した状況（1 または 2）
    payoff_amount = models.IntegerField()    # 最終確定謝礼金（円）


# =========================================================
#  ページ定義
# =========================================================

class Demographics(Page):
    """実験開始前の基本情報入力画面"""
    form_model = 'player'
    form_fields = ['gender', 'age']

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
        your_p = player.practice1_p
        # プレイヤーA(your_p), B(30), C(50) の平均値
        big_p = round((your_p + 30 + 50) / 300.0, 3)
        return {
            'your_p': your_p,
            'big_p': big_p,
            'payoff_s1': int(big_p * 2000),
            'payoff_s2': int((1 - big_p) * 2000),
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
        your_p = player.practice2_p
        # プレイヤーB(your_p), A(70), C(50) の平均値
        big_p = round((70 + your_p + 50) / 300.0, 3)
        return {
            'your_p': your_p,
            'big_p': big_p,
            'payoff_s1': int(big_p * 2000),
            'payoff_s2': int((1 - big_p) * 2000),
        }


# --- 本番意思決定画面 ---

class Decision(Page):
    form_model = 'player'
    form_fields = ['declaration']

    @staticmethod
    def vars_for_template(player: Player):
        r = player.round_number
        id_in_g = player.id_in_group

        # ラウンド別の確率設定（1,2,3番目のプレイヤー順）
        if r in [1, 3]:
            prob1 = 80 if id_in_g == 1 else (50 if id_in_g == 2 else 20)
        else:
            prob1 = 60 if id_in_g == 1 else (50 if id_in_g == 2 else 40)

        # 1: プレイヤーA, 2: プレイヤーB, 3: プレイヤーC
        role_map = {1: 'プレイヤーA', 2: 'プレイヤーB', 3: 'プレイヤーC'}

        # 静的画像の切り替え（playler のタイポを player に修正、1=A, 2=B, 3=C に対応）
        rule_prefix = '3mean' if r <= 2 else '3median'
        role_letter = 'A' if id_in_g == 1 else ('B' if id_in_g == 2 else 'C')
        prob_str = f"{prob1:02d}"
        image_name = f"{rule_prefix}_player{role_letter}_{prob_str}_point.png"

        return {
            'round_num': r,
            'role_name': role_map.get(id_in_g, 'プレイヤーA'),
            'prob_s1': prob1,
            'prob_s2': 100 - prob1,
            'image_name': image_name,
        }


class DecisionWaitPage(WaitPage):
    """毎ラウンドの意思決定後、全員の入力を待って確率 P を計算"""
    @staticmethod
    def after_all_players_arrive(group: Group):
        r = group.round_number
        players = group.get_players()
        declarations = [p.declaration / 100.0 for p in players]

        if r <= 2:
            # 前半（第1・2ラウンド）：平均値ルール
            p_calc = sum(declarations) / 3.0
        else:
            # 後半（第3・4ラウンド）：メジアンルール
            p_calc = float(np.median(declarations))

        group.calculated_P = round(p_calc, 3)


# --- 後半練習3・4（メジアンルール） ---

class Practice3(Page):
    form_model = 'player'
    form_fields = ['practice3_p']

    @staticmethod
    def is_displayed(player: Player):
        # 第2ラウンド（前半本番）終了後、後半練習へ移動
        return player.round_number == 2


class Practice3Results(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 2

    @staticmethod
    def vars_for_template(player: Player):
        your_p = player.practice3_p
        # プレイヤーA(your_p), B(30), C(50) の中央値
        big_p = round(float(np.median([your_p / 100.0, 0.30, 0.50])), 3)
        return {
            'your_p': your_p,
            'big_p': big_p,
            'payoff_s1': int(big_p * 2000),
            'payoff_s2': int((1 - big_p) * 2000),
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
        your_p = player.practice4_p
        # プレイヤーB(your_p), A(70), C(50) の中央値
        big_p = round(float(np.median([0.70, your_p / 100.0, 0.50])), 3)
        return {
            'your_p': your_p,
            'big_p': big_p,
            'payoff_s1': int(big_p * 2000),
            'payoff_s2': int((1 - big_p) * 2000),
        }


# --- 全ラウンド終了時の最終集計処理 ---

class FinalResultsWaitPage(WaitPage):
    """全ラウンド終了後、支払対象ラウンド（1〜4）を1つランダム抽出して確定謝礼金を計算"""
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def after_all_players_arrive(group: Group):
        subsession = group.subsession
        
        # グループ内の全プレイヤーで同じ支払対象ラウンドを選択
        selected_r = random.randint(1, C.NUM_ROUNDS)

        for p in group.get_players():
            # 選ばれたラウンドのプレイヤーおよびグループデータを取得
            target_p = p.in_round(selected_r)
            target_g = group.in_round(selected_r)

            big_p = target_g.calculated_P
            id_in_g = target_p.id_in_group

            # 選定ラウンドでの状況1の発生確率（くじの確率）
            if selected_r in [1, 3]:
                prob1 = 80 if id_in_g == 1 else (50 if id_in_g == 2 else 20)
            else:
                prob1 = 60 if id_in_g == 1 else (50 if id_in_g == 2 else 40)

            # コンピュータによる自動抽選（状況1 または 状況2）
            drawn_state = 1 if random.random() < (prob1 / 100.0) else 2

            # 確定謝礼金の計算
            if drawn_state == 1:
                final_payoff = int(big_p * 2000)
            else:
                final_payoff = int((1.0 - big_p) * 2000)

            # 第4ラウンド（最終結果画面表示用）のフィールドに記録を保持
            final_p_obj = p.in_round(C.NUM_ROUNDS)
            final_p_obj.selected_round = selected_r
            final_p_obj.final_p = big_p
            final_p_obj.chosen_state = drawn_state
            final_p_obj.payoff_amount = final_payoff
            final_p_obj.payoff = final_payoff  # oTree標準の謝礼フィールド


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

        # 全4ラウンド分の履歴データを構築
        for r in range(1, C.NUM_ROUNDS + 1):
            r_player = player.in_round(r)
            r_group = player.group.in_round(r)
            r_players = r_group.get_players()

            my_p = r_player.declaration
            other_decls = [p.declaration for p in r_players if p.id_in_group != r_player.id_in_group]

            id_in_g = r_player.id_in_group
            if r in [1, 3]:
                prob1 = 80 if id_in_g == 1 else (50 if id_in_g == 2 else 20)
            else:
                prob1 = 60 if id_in_g == 1 else (50 if id_in_g == 2 else 40)
            prob2 = 100 - prob1

            calc_p_round = r_group.calculated_P
            amt1 = int(calc_p_round * 2000)
            amt2 = int((1 - calc_p_round) * 2000)

            # 選定ラウンドは確定結果を使用し、それ以外は個別計算
            if r == chosen_r:
                state = player.chosen_state
                round_pay = player.payoff_amount
            else:
                state = 1 if random.random() < (prob1 / 100.0) else 2
                round_pay = amt1 if state == 1 else amt2

            role_map = {1: 'プレイヤーA', 2: 'プレイヤーB', 3: 'プレイヤーC'}

            all_rounds_data.append({
                'round_num': r,
                'role_name': role_map.get(id_in_g, 'プレイヤーA'),
                'my_p': my_p,
                'other_p_1': other_decls[0],
                'other_p_2': other_decls[1],
                'group_P': calc_p_round,
                'prob_result1': prob1,
                'prob_result2': prob2,
                'amount_result1': amt1,
                'amount_result2': amt2,
                'drawn_result': state,
                'round_payoff': round_pay,
            })

        return {
            'selected_round': chosen_r,
            'all_rounds': all_rounds_data,
            'final_payoff': player.payoff_amount,
        }


# =========================================================
#  ページ遷移順序
# =========================================================

page_sequence = [
    Demographics,         # 基本情報入力
    Instructions,         # 全体説明
    # --- 前半（平均値ルール）練習 ---
    Practice1,
    Practice1Results,
    Practice2,
    Practice2Results,
    # --- 本番意思決定（第1〜4ラウンド共通） ---
    Decision,
    DecisionWaitPage,
    # --- 第2ラウンド終了時に挿入される後半練習 ---
    Practice3,
    Practice3Results,
    Practice4,
    Practice4Results,
    # --- 最終結果算出・表示 ---
    FinalResultsWaitPage,
    FinalResults,
]

]
