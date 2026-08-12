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


class Group(BaseGroup):
    group_P = models.FloatField()


class Player(BasePlayer):
    student_id = models.StringField(label="ID（学籍番号など）を入力してください:")
    gender = models.StringField(
        label="戸籍上の性別を選択してください。",
        choices=['男性', '女性'],
        widget=widgets.RadioSelect
    )
    practice_p1 = models.IntegerField(
        label="【プレイヤーAとして】p の値を入力してください（0 〜 100）:",
        min=0,
        max=100
    )
    practice_p2 = models.IntegerField(
        label="【プレイヤーBとして】p の値を入力してください（0 〜 100）:",
        min=0,
        max=100
    )
    p_input = models.IntegerField(
        label="p の値を入力してください（0 〜 100）:",
        min=0,
        max=100
    )
    drawn_result = models.StringField()
    round_payoff = models.FloatField()


# --- PAGES ---

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


class ResultsWaitPage(WaitPage):
    title_text = "集計中"
    body_text = "ペアの入力完了を待っています..."

    @staticmethod
    def after_all_players_arrive(group: Group):
        players = group.get_players()
        # 0〜100 の入力値の平均を取り、100 で割って 0.0〜1.0 の確率 P に変換
        avg_p_int = sum([p.p_input for p in players]) / len(players)
        group.group_P = round(avg_p_int / 100.0, 4)

        P = group.group_P
        r_num = group.round_number
        prob_a_threshold = C.PROBS_A_RESULT1[r_num] / 100.0

        for p in players:
            is_player_a = (p.id_in_group == 1)
            prob_res1_threshold = prob_a_threshold if is_player_a else (1.0 - prob_a_threshold)

            if random.random() < prob_res1_threshold:
                p.drawn_result = "状況 1"
                p.round_payoff = round(P * 2000)
            else:
                p.drawn_result = "状況 2"
                p.round_payoff = round((1 - P) * 2000)

            p.payoff = p.round_payoff

        if group.round_number == C.NUM_ROUNDS:
            for p in players:
                selected_round = random.randint(1, C.NUM_ROUNDS)
                p.participant.vars['selected_round'] = selected_round
                selected_player = p.in_round(selected_round)
                p.participant.payoff = selected_player.round_payoff


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

        return {
            'all_rounds': all_rounds_data,
            'selected_round': selected_round,
            'role_name': role_name,
            'final_payoff': int(player.participant.payoff),
        }


page_sequence = [
    Demographics, 
    DemographicsWaitPage, 
    Instructions,
    Practice, 
    PracticeResults, 
    Practice2, 
    PracticeResults2, 
    Decision, 
    ResultsWaitPage, 
    FinalResults
]
