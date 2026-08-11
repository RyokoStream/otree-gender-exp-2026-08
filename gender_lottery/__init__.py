import random
from otree.api import *

doc = """
Gender Lottery Experiment (Practice 1, Practice 2, Decision with Payoff Randomization)
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
        choices=[[1, 'オプション A（安全）'], [2, 'オプション B（リスク）']],
        widget=widgets.RadioSelect,
        label="【練習1】どちらかのオプションを選択してください。"
    )

    # --- 練習2 ---
    practice2_choice = models.IntegerField(
        choices=[[1, 'オプション A（安全）'], [2, 'オプション B（リスク）']],
        widget=widgets.RadioSelect,
        label="【練習2】異なる条件での選択です。どちらかを選択してください。"
    )

    # --- 本番意思決定（複数質問例：Q1〜Q3） ---
    decision_q1 = models.IntegerField(
        choices=[[1, '確実な 100 円'], [2, '50%で 300 円 / 50%で 0 円']],
        widget=widgets.RadioSelect,
        label="質問 1"
    )
    decision_q2 = models.IntegerField(
        choices=[[1, '確実な 150 円'], [2, '50%で 300 円 / 50%で 0 円']],
        widget=widgets.RadioSelect,
        label="質問 2"
    )
    decision_q3 = models.IntegerField(
        choices=[[1, '確実な 200 円'], [2, '50%で 300 円 / 50%で 0 円']],
        widget=widgets.RadioSelect,
        label="質問 3"
    )

    # --- 抽選結果保存用 ---
    selected_question = models.IntegerField()  # 何番目の質問が選ばれたか (1, 2, 3)
    selected_choice = models.IntegerField()    # その質問で選んだ選択肢 (1:結果1, 2:結果2)
    lottery_outcome = models.StringField()    # 抽選の結果（例: "300円", "0円", "100円"）

# --- FUNCTIONS ---

def set_payoffs(player: Player):
    """最終結果の決定ロジック：質問をランダムに1つ抽出し、結果を計算"""
    # 質問1〜3の中から1つをランダム選択
    player.selected_question = random.randint(1, 3)
    
    # 選択された質問の回答を取得
    if player.selected_question == 1:
        player.selected_choice = player.decision_q1
    elif player.selected_question == 2:
        player.selected_choice = player.decision_q2
    else:
        player.selected_choice = player.decision_q3

    # 選んだ選択肢に応じて結果を判定
    if player.selected_choice == 1:
        # 結果1（安全肢を選んでいた場合）
        if player.selected_question == 1:
            player.lottery_outcome = "確実な 100 円"
        elif player.selected_question == 2:
            player.lottery_outcome = "確実な 150 円"
        else:
            player.lottery_outcome = "確実な 200 円"
    else:
        # 結果2（リスク肢を選んでいた場合：50%で当たり）
        if random.random() < 0.5:
            player.lottery_outcome = "300 円（当たり）"
        else:
            player.lottery_outcome = "0 円（ハズレ）"


# --- PAGES ---

class Instructions(Page):
    pass

class Practice1(Page):
    form_model = 'player'
    form_fields = ['practice1_choice']

class Practice1Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return {
            'choice_label': "オプション A" if player.practice1_choice == 1 else "オプション B"
        }

class Practice2(Page):
    form_model = 'player'
    form_fields = ['practice2_choice']

class Practice2Results(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return {
            'choice_label': "オプション A" if player.practice2_choice == 1 else "オプション B"
        }

class Decision(Page):
    form_model = 'player'
    form_fields = ['decision_q1', 'decision_q2', 'decision_q3']

class ResultsWaitPage(WaitPage):
    """抽選計算を行う処理ページ"""
    after_all_players_arrive = lambda group: None
    
    @staticmethod
    def is_displayed(player: Player):
        set_payoffs(player)
        return True

class Results(Page):
    """最終結果：何番目が選ばれ、どちらの結果になったかを表示"""
    @staticmethod
    def vars_for_template(player: Player):
        selected_option = "結果 1（安全肢）" if player.selected_choice == 1 else "結果 2（リスク肢）"
        return {
            'question_num': player.selected_question,
            'selected_option': selected_option,
            'outcome': player.lottery_outcome,
        }

page_sequence = [
    Instructions,
    Practice1,
    Practice1Results,
    Practice2,
    Practice2Results,
    Decision,
    ResultsWaitPage,
    Results,
]
