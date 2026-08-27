import random
from otree.api import *

doc = """
情報共有型くじ実験（両役体験練習付き）
"""


class C(BaseConstants):
    NAME_IN_URL = 'gender_lottery'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 3
    PROBS_A_RESULT1 = {1: 60, 2: 70, 3: 80}


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    # ラウンド1の時点で、グループごとに支払対象ラウンド（1〜3）を1つ確定させておく
    if subsession.round_number == 1:
        for group in subsession.get_groups():
            group.session.vars[f'selected_round_group_{group.id_in_subsession}'] = random.randint(1, C.NUM_ROUNDS)


class Group(BaseGroup):
    group_P = models.FloatField()


class Player(BasePlayer):
    student_id = models.StringField(label="学生番号")
    gender = models.StringField(
        choices=['男性', '女性', 'その他・回答しない'],
        label="性別"
    )

    # 4つの同意チェックボックス用フィールド
    consent_1 = models.BooleanField(
        label="上記の説明を理解し、同意します",
        widget=widgets.CheckboxInput
    )
    consent_2 = models.BooleanField(
        label="上記の説明を理解し、同意します",
        widget=widgets.CheckboxInput
    )
    consent_3 = models.BooleanField(
        label="上記の説明を理解し、同意します",
        widget=widgets.CheckboxInput
    )
    consent_4 = models.BooleanField(
        label="上記の説明を理解し、同意します",
        widget=widgets.CheckboxInput
    )

    practice_p1 = models.IntegerField(
        label="【プレイヤーAとして】p の値を入力してください（0 〜 100）:",
        min=0, max=100
    )
    practice_p2 = models.IntegerField(
        label="【プレイヤーBとして】p の値を入力してください（0 〜 100）:",
        min=0, max=100
    )
    p_input = models.IntegerField(
        label="p の値を入力してください（0 〜 100）:",
        min=0, max=100
    )
    drawn_result = models.StringField()
    choice_payoff = models.FloatField()
    round_payoff = models.FloatField()


# --- PAGES ---

class Consent(Page):
    """一番最初に表示する同意書"""
    form_model = 'player'
    form_fields = ['consent_1', 'consent_2', 'consent_3', 'consent_4']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class Demographics(Page):
    form_model = 'player'
    form_fields = ['student_id', 'gender']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class DemographicsWaitPage(WaitPage):
    title_text = "待機中"
    body_text = "ペアの相手が入力するのを待っています..."

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class PaymentInstruction(Page):
    """報酬ルールの説明"""
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class Instructions(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class Practice(Page):
    """練習1（プレイヤーAの立場）"""
    form_model = 'player'
    form_fields = ['practice_p1']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class PracticeResults(Page):
    """練習1の結果"""
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        my_p_int = player.practice_p1
        my_p_ratio = my_p_int / 100.0
        other_p_ratio = 0.50
        group_P = round((my_p_ratio + other_p_ratio) / 2, 4)
        return {
            'my_p': my_p_int,
            'other_p': 50,
            'group_P': group_P,
            'amount_result1': round(group_P * 2000),
            'amount_result2': round((1 - group_P) * 2000),
        }


class Practice2(Page):
    """練習2（プレイヤーBの立場）"""
    form_model = 'player'
    form_fields = ['practice_p2']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class PracticeResults2(Page):
    """練習2の結果"""
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        my_p_int = player.practice_p2
        my_p_ratio = my_p_int / 100.0
        other_p_ratio = 0.50
        group_P = round((my_p_ratio + other_p_ratio) / 2, 4)
        return {
            'my_p': my_p_int,
            'other_p': 50,
            'group_P': group_P,
            'amount_result1': round(group_P * 2000),
            'amount_result2': round((1 - group_P) * 2000),
        }


class Decision(Page):
    form_model = 'player'
    form_fields = ['p_input']

    @staticmethod
    def vars_for_template(player: Player):
        other_player = player.get_others_in_group()[0]
        first_other = other_player.in_round(1)
        is_player_a = (player.id_in_group == 1)
        r_num = player.round_number
        prob_a_res1 = C.PROBS_A_RESULT1[r_num]
        prob_a_res2 = 100 - prob_a_res1

        if is_player_a:
            role_name = "プレイヤーA"
            prob_result1 = prob_a_res1
            prob_result2 = prob_a_res2
        else:
            role_name = "プレイヤーB"
            prob_result1 = prob_a_res2
            prob_result2 = prob_a_res1

        return {
            'role_name': role_name,
            'other_id': first_other.student_id,
            'other_gender': first_other.gender,
            'prob_result1': prob_result1,
            'prob_result2': prob_result2,
            'round_num': r_num,
        }


# --- 成果集計・最終謝礼決定 ---
class ResultsWaitPage(WaitPage):
    title_text = "集計中"
    body_text = "ペアの入力完了を待っています..."

    @staticmethod
    def after_all_players_arrive(group: Group):
        players = group.get_players()
        p1 = players[0]
        p2 = players[1]

        # 1. 宣言された p の平均値から P を計算 (0.0 〜 1.0)
        p1_val = p1.p_input if p1.p_input is not None else 50
        p2_val = p2.p_input if p2.p_input is not None else 50
        group.group_P = (p1_val + p2_val) / 200.0

        # 2. ラウンドごとの得られる金額決定（利得フレーム）
        round_num = group.round_number
        prob_res1 = C.PROBS_A_RESULT1.get(round_num, 50) / 100.0
        is_result1 = random.random() < prob_res1

        for p in players:
            p.drawn_result = "状況1" if is_result1 else "状況2"

            if p.id_in_group == 1:  # プレイヤーA
                if is_result1:
                    p.choice_payoff = group.group_P * 2000  # 利得: P × 2000円
                else:
                    p.choice_payoff = (1.0 - group.group_P) * 2000  # 利得: (1 - P) × 2000円
            else:  # プレイヤーB
                if is_result1:
                    p.choice_payoff = (1.0 - group.group_P) * 2000  # 利得: (1 - P) × 2000円
                else:
                    p.choice_payoff = group.group_P * 2000  # 利得: P × 2000円

            p.round_payoff = p.choice_payoff

        # 3. 最終ラウンド終了時の清算処理（1/4 ずつの二段階抽選）
        if group.round_number == C.NUM_ROUNDS:
            for p in players:
                # 【第1段階】4つの選択肢から 1/4 (25%) で選出
                category_choice = random.choice(['consensus_r1', 'consensus_r2', 'consensus_r3', 'slider_task'])

                if category_choice.startswith('consensus_r'):
                    target_round = int(category_choice.replace('consensus_r', ''))
                    selected_player = p.in_round(target_round)
                    p.participant.vars['selected_round'] = target_round
                    final_choice = {
                        'task_type': 'gender_lottery',
                        'title': f'合意形成タスク（第{target_round}ラウンド）',
                        'payoff': selected_player.round_payoff,
                    }
                    p.participant.vars['final_choice_detail'] = final_choice
                    p.participant.payoff = final_choice['payoff']
                else:
                    # 【第2段階】確実等価性タスク（CE）
                    q_num = random.randint(1, 22)
                    slider_answers = p.participant.vars.get('slider_answers', {})
                    sure_payoffs = p.participant.vars.get('slider_sure_payoffs', [])
                    slider_high = p.participant.vars.get('slider_lottery_high', 2000)
                    slider_low = p.participant.vars.get('slider_lottery_low', 0)

                    chosen_lottery = slider_answers.get(q_num, True)
                    final_choice = {
                        'task_type': 'slider',
                        'title': f'確実等価性タスク（第{q_num}問）',
                        'is_lottery': chosen_lottery,
                        'sure_payoff': sure_payoffs[q_num - 1] if q_num - 1 < len(sure_payoffs) else 0,
                        'high': slider_high,
                        'low': slider_low,
                    }
                    p.participant.vars['final_choice_detail'] = final_choice

                    if final_choice['is_lottery']:
                        won = random.random() < 0.5
                        p.participant.payoff = final_choice['high'] if won else final_choice['low']
                    else:
                        p.participant.payoff = final_choice['sure_payoff']


class FinalResults(Page):
    """全3回終了後の最終清算画面"""
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        all_rounds_data = []
        is_player_a = (player.id_in_group == 1)
        role_name = "プレイヤーA" if is_player_a else "プレイヤーB"

        for p in player.in_all_rounds():
            r_num = p.round_number
            other_p = p.get_others_in_group()[0]
            prob_a_res1 = C.PROBS_A_RESULT1[r_num]
            prob_a_res2 = 100 - prob_a_res1
            prob_result1 = prob_a_res1 if is_player_a else prob_a_res2
            prob_result2 = prob_a_res2 if is_player_a else prob_a_res1
            group_P = p.group.group_P

            all_rounds_data.append({
                'round_num': r_num,
                'my_p': p.p_input,
                'other_p': other_p.p_input,
                'group_P': group_P,
                'prob_result1': prob_result1,
                'prob_result2': prob_result2,
                'amount_result1': round(group_P * 2000),
                'amount_result2': round((1 - group_P) * 2000),
                'drawn_result': p.drawn_result,
                'round_payoff': int(p.round_payoff),
            })

        selected_round = player.participant.vars.get('selected_round', 1)
        final_detail = player.participant.vars.get('final_choice_detail', {})

        return {
            'all_rounds': all_rounds_data,
            'selected_round': selected_round,
            'role_name': role_name,
            'final_detail': final_detail,
            'final_payoff': int(player.participant.payoff),
        }


page_sequence = [
    Consent,              # 1. 一番最初に同意
    Demographics,
    DemographicsWaitPage,
    PaymentInstruction,   # 3. 報酬ルールの説明
    Instructions,
    Practice,
    PracticeResults,
    Practice2,
    PracticeResults2,
    Decision,
    ResultsWaitPage,
    FinalResults
]
