from otree.api import *

doc = """
研究参加への同意取得（ペア単位の判定つき）。
app_sequence の先頭に置くこと。以降の全アプリは
participant.vars['pair_consented'] を見て表示可否を決める。
"""


class C(BaseConstants):
    NAME_IN_URL = 'consent'
    PLAYERS_PER_GROUP = 2   # gender_lottery と同じ人数にすること（同じペアになる）
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    consent_1 = models.StringField(
        choices=['同意する', '同意しない'],
        widget=widgets.RadioSelect
    )
    consent_2 = models.StringField(
        choices=['同意する', '同意しない'],
        widget=widgets.RadioSelect
    )
    consent_3 = models.StringField(
        choices=['同意する', '同意しない'],
        widget=widgets.RadioSelect
    )
    consent_4 = models.StringField(
        choices=['同意する', '同意しない'],
        widget=widgets.RadioSelect
    )

    @property
    def consented(self):
        """4項目すべてに『同意する』を選んだ場合のみ True。未入力(None)は False。"""
        return all([
            self.consent_1 == '同意する',
            self.consent_2 == '同意する',
            self.consent_3 == '同意する',
            self.consent_4 == '同意する',
        ])


# --- PAGES ---

class Consent(Page):
    """一番最初に表示する同意書"""
    form_model = 'player'
    form_fields = ['consent_1', 'consent_2', 'consent_3', 'consent_4']


class ConsentWaitPage(WaitPage):
    """
    両者の同意入力が揃うまで待つ。
    これが無いと、相手の consent_* が None のまま判定されてすり抜ける。
    判定結果を participant.vars に書き出し、以降のアプリから参照できるようにする。
    """
    title_text = "待機中"
    body_text = "ペアの相手の手続きを待っています..."

    @staticmethod
    def after_all_players_arrive(group: Group):
        players = group.get_players()
        both_ok = all(p.consented for p in players)
        for p in players:
            p.participant.vars['consented'] = p.consented
            p.participant.vars['pair_consented'] = both_ok


class Refusal(Page):
    """自分が『同意しない』を選んだ場合に表示"""
    @staticmethod
    def is_displayed(player: Player):
        return not player.consented


class PartnerRefusal(Page):
    """自分は同意したが、ペアの相手が同意しなかった場合に表示"""
    @staticmethod
    def is_displayed(player: Player):
        if not player.consented:
            return False
        others = player.get_others_in_group()
        if not others:
            return False
        return not others[0].consented


page_sequence = [
    Consent,
    ConsentWaitPage,
    Refusal,
    PartnerRefusal,
]
