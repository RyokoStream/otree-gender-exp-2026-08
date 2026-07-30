from otree.api import *
import random

class C(BaseConstants):
    NAME_IN_URL = 'mpl'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    ROWS = [
        dict(row=1,  p_high=0.1),
        dict(row=2,  p_high=0.2),
        dict(row=3,  p_high=0.3),
        dict(row=4,  p_high=0.4),
        dict(row=5,  p_high=0.5),
        dict(row=6,  p_high=0.6),
        dict(row=7,  p_high=0.7),
        dict(row=8,  p_high=0.8),
        dict(row=9,  p_high=0.9),
        dict(row=10, p_high=1.0),
    ]

    A_HIGH = cu(200)
    A_LOW  = cu(160)
    B_HIGH = cu(385)
    B_LOW  = cu(10)

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    choice_1  = models.IntegerField(choices=[(1, 'A'), (2, 'B')], widget=widgets.RadioSelectHorizontal)
    choice_2  = models.IntegerField(choices=[(1, 'A'), (2, 'B')], widget=widgets.RadioSelectHorizontal)
    choice_3  = models.IntegerField(choices=[(1, 'A'), (2, 'B')], widget=widgets.RadioSelectHorizontal)
    choice_4  = models.IntegerField(choices=[(1, 'A'), (2, 'B')], widget=widgets.RadioSelectHorizontal)
    choice_5  = models.IntegerField(choices=[(1, 'A'), (2, 'B')], widget=widgets.RadioSelectHorizontal)
    choice_6  = models.IntegerField(choices=[(1, 'A'), (2, 'B')], widget=widgets.RadioSelectHorizontal)
    choice_7  = models.IntegerField(choices=[(1, 'A'), (2, 'B')], widget=widgets.RadioSelectHorizontal)
    choice_8  = models.IntegerField(choices=[(1, 'A'), (2, 'B')], widget=widgets.RadioSelectHorizontal)
    choice_9  = models.IntegerField(choices=[(1, 'A'), (2, 'B')], widget=widgets.RadioSelectHorizontal)
    choice_10 = models.IntegerField(choices=[(1, 'A'), (2, 'B')], widget=widgets.RadioSelectHorizontal)

    paying_row        = models.IntegerField()
    paying_choice     = models.IntegerField()
    paying_draw_high  = models.BooleanField()
    payoff_points     = models.CurrencyField()

    switching_row     = models.IntegerField()

    def set_payoff_from_choices(self):
        self.paying_row = random.randint(1, 10)
        cfield = f'choice_{self.paying_row}'
        self.paying_choice = getattr(self, cfield)

        p_high = C.ROWS[self.paying_row - 1]['p_high']
        draw_high = random.random() < p_high
        self.paying_draw_high = draw_high

        if self.paying_choice == 1:
            amount = C.A_HIGH if draw_high else C.A_LOW
        else:
            amount = C.B_HIGH if draw_high else C.B_LOW

        self.payoff_points = amount
        self.payoff = amount

    def compute_switching_row(self):
        choices = [getattr(self, f'choice_{i}') for i in range(1, 11)]
        try:
            idx = choices.index(2)
            self.switching_row = idx + 1
        except ValueError:
            self.switching_row = 11

class Intro(Page):
    pass

class MPL(Page):
    form_model = 'player'
    form_fields = [f'choice_{i}' for i in range(1, 11)]

    @staticmethod
    def vars_for_template(player):
        # テンプレ用（表示整形はPython側で）
        rows = []
        for r in C.ROWS:
            p_high = r['p_high']
            p_low  = 1 - p_high
            rows.append(dict(
                row=r['row'],
                p_high=p_high,
                p_low=p_low,
                p_high_str=f'{p_high:.1f}',
                p_low_str=f'{p_low:.1f}',
                A_high=C.A_HIGH, A_low=C.A_LOW,
                B_high=C.B_HIGH, B_low=C.B_LOW,
                field_name=f"choice_{r['row']}",
            ))
        return dict(rows=rows)

    @staticmethod
    def before_next_page(player, timeout_happened=False):
        player.compute_switching_row()
        player.set_payoff_from_choices()


class Results(Page):
    @staticmethod
    def vars_for_template(player):
        r = player.paying_row
        p_high = C.ROWS[r - 1]['p_high']
        return dict(
            target=dict(
                row=r,
                p_high=p_high,
                p_low=1 - p_high,
                choice=('A' if player.paying_choice == 1 else 'B'),
                draw=('High' if player.paying_draw_high else 'Low'),
                amount=player.payoff_points,
            )
        )



page_sequence = [Intro, MPL, Results]





