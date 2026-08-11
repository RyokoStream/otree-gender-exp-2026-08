import random
from otree.api import *

doc = """
Gender Lottery Experiment (Practice 1-2, Sequential Decisions 1-3, FinalResult)
"""

class C(BaseConstants):
    NAME_IN_URL = 'gender_lottery'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # --- 練習1 ---
    practice1_choice = models.IntegerField(
        choices=[[1, '結果 1'], [2, '結果 2']],
        widget=widgets.RadioSelect,
        label="【練習1】どちらかを選択してください。"
    )

    # --- 練習2 ---
    practice2_choice = models.IntegerField(
        choices=[[1, '結果 1'], [2, '結果 2']],
        widget=widgets.RadioSelect,
        label="【練習2】どちらかを選択してください。"
    )

    # --- 本番1〜3 ---
    decision1_choice = models.IntegerField(
        choices=[[1, '結果 1'], [2, '結果 2']],
        widget=widgets.RadioSelect,
        label="【本番 1/3】どちらかを選択してください。"
    )

    decision2_choice = models.IntegerField(
        choices=[[1, '結果 1'], [2, '結果 2']],
        widget=widgets.RadioSelect,
        label="【本番 2/3】どちらかを選択してください。"
    )

    decision3_choice = models.IntegerField(
        choices=[[1, '結果 1'], [2, '結果 2']],
        widget=widgets.RadioSelect,
        label="【本番 3/3】どちらかを選択してください。"
    )

    # --- 抽選結果記録用 ---
    selected_decision = models.IntegerField()  # 1, 2, 3のいずれか
    selected_choice = models.IntegerField()    # 1（結果1） または 2（結果2）
    final_outcome = models.StringField()      # 最終判定結果


def set_payoffs(player: Player):
    # 3回の本番から1つをランダムに選出
    chosen_num = random.randint(1, 3)
    player.selected_decision = chosen_num

    # 選ばれた本番でプレイヤーが選択していた回答を取得
    if chosen_num == 1:
        player.selected_choice = player.decision1_choice
    elif chosen_num == 2:
        player.selected_choice = player.decision2_choice
    else:
        player.selected_choice = player.decision3_choice

    # 選択に基づく最終結果の判定
    if player.selected_choice == 1:
        player.final_outcome = "結果 1"
    else:
        player.final_outcome = "結果 2"


# --- PAGES ---

class Instructions(Page):
    pass


class Practice1(Page):
    form_model = 'player'
    form_fields = ['practice1_choice']


class Practice1Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return {'choice_label': "結果 1" if player.practice1_choice == 1 else "結果 2"}


class Practice2(Page):
    form_model = 'player'
    form_fields = ['practice2_choice']


class Practice2Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return {'choice_label': "結果 1" if player.practice2_choice == 1 else "結果 2"}


class Decision1(Page):
    form_model = 'player'
    form_fields = ['decision1_choice']


class Decision2(Page):
    form_model = 'player'
    form_fields = ['decision2_choice']


class Decision3(Page):
    form_model = 'player'
    form_fields = ['decision3_choice']


class ResultsWaitPage(WaitPage):
    pass


class FinalResult(Page):
    @staticmethod
    def vars_for_template(player: Player):
        set_payoffs(player)
        selected_choice_text = "結果 1" if player.selected_choice == 1 else "結果 2"
        return {
            'selected_decision': player.selected_decision,
            'selected_choice_text': selected_choice_text,
            'final_outcome': player.final_outcome,
        }


page_sequence = [
    Instructions,
    Practice1,
    Practice1Results,
    Practice2,
    Practice2Results,
    Decision1,
    Decision2,
    Decision3,
    ResultsWaitPage,
    FinalResult,
]
