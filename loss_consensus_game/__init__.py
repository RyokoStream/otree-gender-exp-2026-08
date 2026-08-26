import random
from otree.api import *

doc = """
情報共有型くじ実験（集団合意形成ゲーム・損失フレーム）
"""


class C(BaseConstants):
    NAME_IN_URL = 'loss_consensus_game'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 3

    # 初期手元金（円）
    ENDOWMENT = 2000

    # ラウンドごとの【状況1】が発生する確率（%）
    PROBS_RESULT1 = {1: 60, 2: 70, 3: 80}


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    # 二人が入力した p の平均値 (0.00 ~ 1.00)
    group_P = models.FloatField()


class Player(BasePlayer):
    student_id = models.StringField(label="もらっているID番号を入力してください。学籍番号を入力しないように:")
    gender = models.StringField(label="戸籍上の性別を選択してください:", choices=['男性', '女性'], widget=widgets.RadioSelect)

    # --- 練習ラウンド用 p の値 (0 〜 100) ---
    practice_p_1 = models.IntegerField(min=0, max=100, label="練習1: あなたにとって望ましい p の値 (0〜100)")
    practice_p_2 = models.IntegerField(min=0, max=100, label="練習2: あなたにとって望ましい p の値 (0〜100)")

    # --- 本番ラウンド用 p の値 (0 〜 100) ---
    p_value = models.IntegerField(min=0, max=100, label="あなたにとって望ましい p の値 (0〜100)")

    # 利得・損失計算保持用
    choice_loss = models.FloatField()
    round_payoff = models.FloatField()


# =========================================================
# PAGES
# =========================================================

class Demographics(Page):
    form_model = 'player'
    form_fields = ['student_id', 'gender']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class DemographicsWaitPage(WaitPage):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class Instructions(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


# --- 練習 1 ---
class Practice1(Page):
    form_model = 'player'
    form_fields = ['practice_p_1']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class PracticeResults(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        dummy_other_p = 50
        p_A = player.practice_p_1 if player.practice_p_1 is not None else 50
        calc_P = (p_A + dummy_other_p) / 200.0  # 平均のP (0.0~1.0)
        
        # 仮の状況（状況1が発生したと仮定）
        p_loss = (1.0 - calc_P) * C.ENDOWMENT
        total_p_payoff = C.ENDOWMENT - p_loss

        return {
            'dummy_other_p': dummy_other_p,
            'calc_P_percent': int(calc_P * 100),
            'p_loss': int(p_loss),
            'total_payoff': int(total_p_payoff)
        }


# --- 練習 2 ---
class Practice2(Page):
    form_model = 'player'
    form_fields = ['practice_p_2']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class PracticeResults2(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        dummy_other_p = 40
        p_B = player.practice_p_2 if player.practice_p_2 is not None else 40
        calc_P = (p_B + dummy_other_p) / 200.0
        
        p_loss = calc_P * C.ENDOWMENT
        total_p_payoff = C.ENDOWMENT - p_loss

        return {
            'dummy_other_p': dummy_other_p,
            'calc_P_percent': int(calc_P * 100),
            'p_loss': int(p_loss),
            'total_payoff': int(total_p_payoff)
        }


# --- 本番意思決定 ---
class Decision(Page):
    form_model = 'player'
    form_fields = ['p_value']

    @staticmethod
    def vars_for_template(player: Player):
        round_num = player.round_number
        prob_res1 = C.PROBS_RESULT1.get(round_num, 50)
        prob_res2 = 100 - prob_res1

        # ペア相手の性別取得
        other_player = player.get_others_in_group()[0]
        other_gender = other_player.gender if other_player.gender else "未回答"

        role_name = "プレイヤーA" if player.id_in_group == 1 else "プレイヤーB"

        return {
            'round_num': round_num,
            'prob_result1': prob_res1,
            'prob_result2': prob_res2,
            'other_gender': other_gender,
            'role_name': role_name,
        }


# --- 成果集計・最終謝礼決定 ---
class ResultsWaitPage(WaitPage):
    @staticmethod
    def after_all_players_arrive(group: Group):
        players = group.get_players()
        p1 = players[0]
        p2 = players[1]

        # 1. 宣言された p の平均値から P を計算 (0.0 〜 1.0)
        p1_val = p1.p_value if p1.p_value is not None else 50
        p2_val = p2.p_value if p2.p_value is not None else 50
        group.group_P = (p1_val + p2_val) / 200.0

        # 2. ラウンドごとの損失決定（状況1 か 状況2 かをランダム決定）
        round_num = group.round_number
        prob_res1 = C.PROBS_RESULT1.get(round_num, 50) / 100.0
        is_result1 = random.random() < prob_res1

        for p in players:
            if p.id_in_group == 1:  # プレイヤーA
                if is_result1:
                    p.choice_loss = (1.0 - group.group_P) * C.ENDOWMENT
                else:
                    p.choice_loss = group.group_P * C.ENDOWMENT
            else:  # プレイヤーB
                if is_result1:
                    p.choice_loss = group.group_P * C.ENDOWMENT
                else:
                    p.choice_loss = (1.0 - group.group_P) * C.ENDOWMENT

            p.round_payoff = C.ENDOWMENT - p.choice_loss

        # 3. 最終ラウンド終了時の清算処理
        if group.round_number == C.NUM_ROUNDS:
            for p in players:
                candidates = []

                # A) part1_slider_risk の全22問を追加
                slider_answers = p.participant.vars.get('slider_answers', {})
                sure_payoffs = p.participant.vars.get('slider_sure_payoffs', [])
                slider_high = p.participant.vars.get('slider_lottery_high', 2000)
                slider_low = p.participant.vars.get('slider_lottery_low', 0)

                for q_num, chosen_lottery in slider_answers.items():
                    candidates.append({
                        'task_type': 'slider',
                        'title': f'確定等価性タスク（第{q_num}問）',
                        'is_lottery': chosen_lottery,
                        'sure_payoff': sure_payoffs[q_num - 1] if q_num - 1 < len(sure_payoffs) else 0,
                        'high': slider_high,
                        'low': slider_low,
                    })

                # B) loss_consensus_game の3ラウンドを追加
                for r_num in range(1, C.NUM_ROUNDS + 1):
                    p_in_r = p.in_round(r_num)
                    candidates.append({
                        'task_type': 'loss_consensus',
                        'title': f'合意形成タスク（第{r_num}ラウンド）',
                        'payoff': p_in_r.round_payoff,
                    })

                # C) 全25問（22+3）からランダムで1つ選出
                if candidates:
                    final_choice = random.choice(candidates)
                    p.participant.vars['final_choice_detail'] = final_choice

                    if final_choice['task_type'] == 'loss_consensus':
                        p.participant.payoff = final_choice['payoff']
                    else:
                        if final_choice['is_lottery']:
                            won = random.random() < 0.5
                            p.participant.payoff = final_choice['high'] if won else final_choice['low']
                        else:
                            p.participant.payoff = final_choice['sure_payoff']


class FinalResults(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        final_detail = player.participant.vars.get('final_choice_detail', {})
        return {
            'final_detail': final_detail,
            'final_payoff': int(player.participant.payoff),
        }


# =========================================================
# PAGE SEQUENCE
# =========================================================

page_sequence = [
    Demographics,
    DemographicsWaitPage,
    Instructions,
    Practice1,
    PracticeResults,
    Practice2,
    PracticeResults2,
    Decision,
    ResultsWaitPage,
    FinalResults
]
