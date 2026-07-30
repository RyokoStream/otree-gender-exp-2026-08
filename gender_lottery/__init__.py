import random
from otree.api import *

doc = """
情報共有型くじ実験
"""

class C(BaseConstants):
    NAME_IN_URL = 'gender_lottery'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    # 集計された P の値（2人の入力の平均値）
    group_P = models.FloatField()


class Player(BasePlayer):
    # 性別選択
    gender = models.StringField(
        label="あなたの性別を選択してください。",
        choices=['男性', '女性', 'その他・回答しない'],
        widget=widgets.RadioSelect
    )
    # p の入力（0.0 から 1.0 の間）
    p_input = models.FloatField(
        label="p の値を入力してください（0.0 〜 1.0）:",
        min=0.0,
        max=1.0
    )
    # 抽選結果と最終確定金額
    drawn_result = models.StringField()
    final_payoff = models.FloatField()


# --- PAGES ---

class Demographics(Page):
    form_model = 'player'
    form_fields = ['gender']


class DemographicsWaitPage(WaitPage):
    title_text = "待機中"
    body_text = "ペアの相手が入力するのを待っています..."


class Decision(Page):
    form_model = 'player'
    form_fields = ['p_input']

    @staticmethod
    def vars_for_template(player: Player):
        other_player = player.get_others_in_group()[0]
        
        is_player_a = (player.id_in_group == 1)
        
        if is_player_a:
            role_name = "プレイヤーA"
            prob_result1 = 70
            prob_result2 = 30
        else:
            role_name = "プレイヤーB"
            prob_result1 = 30
            prob_result2 = 70

        return {
            'role_name': role_name,
            'other_gender': other_player.gender,
            'prob_result1': prob_result1,
            'prob_result2': prob_result2,
        }


class ResultsWaitPage(WaitPage):
    title_text = "集計中"
    body_text = "全員の入力値を集計し、くじの抽選を行っています..."

    @staticmethod
    def after_all_players_arrive(group: Group):
        players = group.get_players()
        # 2人の入力値の平均を計算して集計 P とする
        avg_p = sum([p.p_input for p in players]) / len(players)
        group.group_P = round(avg_p, 4)

        P = group.group_P

        # プレイヤーごとに確率に従って自動抽選を実施
        for p in players:
            is_player_a = (p.id_in_group == 1)
            prob_res1_threshold = 0.70 if is_player_a else 0.30

            # 乱数を使って 確率に応じ「結果1」か「結果2」を決定
            if random.random() < prob_res1_threshold:
                p.drawn_result = "結果 1"
                p.final_payoff = round(P * 100, 2)
            else:
                p.drawn_result = "結果 2"
                p.final_payoff = round((1 - P) * 100, 2)

            # oTree標準の利得フィールドにも保存
            p.payoff = p.final_payoff


class Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        group = player.group
        other_player = player.get_others_in_group()[0]
        
        is_player_a = (player.id_in_group == 1)
        role_name = "プレイヤーA" if is_player_a else "プレイヤーB"
        
        if is_player_a:
            prob_result1 = 70
            prob_result2 = 30
        else:
            prob_result1 = 30
            prob_result2 = 70

        P = group.group_P
        
        amount_result1 = round(P * 100, 2)
        amount_result2 = round((1 - P) * 100, 2)

        return {
            'role_name': role_name,
            'my_p': player.p_input,
            'other_p': other_player.p_input,
            'group_P': P,
            'prob_result1': prob_result1,
            'prob_result2': prob_result2,
            'amount_result1': amount_result1,
            'amount_result2': amount_result2,
            'drawn_result': player.drawn_result,
            'final_payoff': player.final_payoff,
        }


page_sequence = [
    Demographics, 
    DemographicsWaitPage, 
    Decision, 
    ResultsWaitPage, 
    Results
]