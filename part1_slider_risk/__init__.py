import random
from otree.api import *

doc = """
スライダー形式の確定等価性（CE）測定タスク（合体用）
"""

class Constants(BaseConstants):
    name_in_url = 'part1_slider_risk'
    players_per_group = None
    num_rounds = 1

    LOTTERY_HIGH = 2000
    LOTTERY_LOW = 0

    SURE_PAYOFFS = [50 * i for i in range(1, 23)]
    NUM_QUESTIONS = len(SURE_PAYOFFS)


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    switching_point = models.IntegerField(
        min=0,
        max=Constants.NUM_QUESTIONS,
        doc="くじを選んだ最後の問題番号（0〜22）"
    )

    q1 = models.BooleanField()
    q2 = models.BooleanField()
    q3 = models.BooleanField()
    q4 = models.BooleanField()
    q5 = models.BooleanField()
    q6 = models.BooleanField()
    q7 = models.BooleanField()
    q8 = models.BooleanField()
    q9 = models.BooleanField()
    q10 = models.BooleanField()
    q11 = models.BooleanField()
    q12 = models.BooleanField()
    q13 = models.BooleanField()
    q14 = models.BooleanField()
    q15 = models.BooleanField()
    q16 = models.BooleanField()
    q17 = models.BooleanField()
    q18 = models.BooleanField()
    q19 = models.BooleanField()
    q20 = models.BooleanField()
    q21 = models.BooleanField()
    q22 = models.BooleanField()


class Decision(Page):
    form_model = 'player'
    form_fields = ['switching_point'] + [f'q{i}' for i in range(1, 23)]

    def vars_for_template(player: Player):
        questions = []
        for i, sure_payoff in enumerate(Constants.SURE_PAYOFFS, start=1):
            questions.append({
                'num': i,
                'sure_payoff': sure_payoff,
                'high': Constants.LOTTERY_HIGH,
                'low': Constants.LOTTERY_LOW,
            })
        return {
            'questions': questions,
            'num_questions': Constants.NUM_QUESTIONS,
        }

    def before_next_page(player: Player, timeout_happened):
        # 回答データをparticipant.varsに保存して次のアプリ（gender_lottery）へ引き継ぐ
        answers = {}
        for i in range(1, Constants.NUM_QUESTIONS + 1):
            answers[i] = getattr(player, f'q{i}')
        
        player.participant.vars['slider_answers'] = answers
        player.participant.vars['slider_sure_payoffs'] = Constants.SURE_PAYOFFS
        player.participant.vars['slider_lottery_high'] = Constants.LOTTERY_HIGH
        player.participant.vars['slider_lottery_low'] = Constants.LOTTERY_LOW


# 途中で Results ページは挟まず、回答したらそのまま次のアプリへ移動
page_sequence = [Decision]
