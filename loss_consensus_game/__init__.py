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


def creating_session(subsession: Subsession):
    # ラウンド1の時点で、グループごとに支払対象ラウンド（1〜3）を1つ確定させておく
    if subsession.round_number == 1:
        for group in subsession.get_groups():
            group.session.vars[f'selected_round_group_{group.id_in_subsession}'] = random.randint(1, C.NUM_ROUNDS)


class Group(BaseGroup):
    # 二人が入力した p の平均値 (0.00 ~ 1.00)
    group_P = models.FloatField()


class Player(BasePlayer):
    student_id = models.StringField(label="もらっているID番号を入力してください。学籍番号を入力しないように:")
    gender = models.StringField(
        label="戸籍上の性別を選択してください:",
        choices=['男性', '女性'],
        widget=widgets.RadioSelect
    )
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
    title_text = "待機中"
    body_text = "ペアの相手が入力するのを待っています..."

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


# --- 練習 1 結果 ---
class PracticeResults(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        other_p = 50
        my_p = player.practice_p_1 if player.practice_p_1 is not None else 50
        calc_P = (my_p + other_p) / 200.0
        
        loss_res1 = int(calc_P * C.ENDOWMENT)
        loss_res2 = int((1.0 - calc_P) * C.ENDOWMENT)

        return {
            'my_p': my_p,                            # HTMLの {{ my_p }}
            'other_p': other_p,                      # HTMLの {{ other_p }}
            'group_P': f"{calc_P * 100:.1f}%",       # HTMLの {{ group_P }}
            'loss_result1': loss_res1,
            'amount_result1': C.ENDOWMENT - loss_res1,
            'loss_result2': loss_res2,
            'amount_result2': C.ENDOWMENT - loss_res2,
        }


# --- 練習 2 ---
class Practice2(Page):
    form_model = 'player'
    form_fields = ['practice_p_2']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


# --- 練習 2 結果 ---
class PracticeResults2(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        other_p = 40
        my_p = player.practice_p_2 if player.practice_p_2 is not None else 40
        calc_P = (my_p + other_p) / 200.0
        
        loss_res1 = int(calc_P * C.ENDOWMENT)
        loss_res2 = int((1.0 - calc_P) * C.ENDOWMENT)

        return {
            'my_p': my_p,                            # HTMLの {{ my_p }}
            'other_p': other_p,                      # HTMLの {{ other_p }}
            'group_P': f"{calc_P * 100:.1f}%",       # HTMLの {{ group_P }}
            'loss_result1': loss_res1,
            'amount_result1': C.ENDOWMENT - loss_res1,
            'loss_result2': loss_res2,
            'amount_result2': C.ENDOWMENT - loss_res2,
        }


# --- 本番意思決定 ---
class Decision(Page):
    form_model = 'player'
    form_fields = ['p_value']

    @staticmethod
    def vars_for_template(player: Player):
        # 1. 相手プレイヤーのインスタンスを取得
        other_player = player.get_others_in_group()[0]
        # 2. 第1ラウンドで入力された相手情報を取得
        first_other = other_player.in_round(1)

        round_num = player.round_number
        prob_res1 = C.PROBS_RESULT1.get(round_num, 50)
        prob_res2 = 100 - prob_res1

        role_name = "プレイヤーA" if player.id_in_group == 1 else "プレイヤーB"

        return {
            'round_num': round_num,
            'prob_result1': prob_res1,
            'prob_result2': prob_res2,
            'other_id': first_other.student_id,
            'other_gender': first_other.gender,
            'role_name': role_name,
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
            selected_round = group.session.vars.get(
                f'selected_round_group_{group.id_in_subsession}',
                random.randint(1, C.NUM_ROUNDS)
            )

            for p in players:
                p.participant.vars['selected_round'] = selected_round

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

                # B) 本タスク（合意形成タスク）から選ばれた1ラウンド分を追加
                selected_player = p.in_round(selected_round)
                candidates.append({
                    'task_type': 'loss_consensus',
                    'title': f'合意形成タスク（第{selected_round}ラウンド）',
                    'payoff': selected_player.round_payoff,
                })

                # C) 全件からランダムで1つ選出
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
        selected_round = player.participant.vars.get('selected_round', 1)

        # 全3ラウンド分の記録を取得・計算
        all_rounds = []
        for r in player.in_all_rounds():
            other_p = r.get_others_in_group()[0].p_value if r.get_others_in_group()[0].p_value is not None else 50
            my_p = r.p_value if r.p_value is not None else 50
            calc_P = (my_p + other_p) / 200.0

            loss_res1 = int(calc_P * C.ENDOWMENT)
            loss_res2 = int((1.0 - calc_P) * C.ENDOWMENT)

            prob_res1 = C.PROBS_RESULT1.get(r.round_number, 50)
            prob_res2 = 100 - prob_res1

            # 状況1か状況2かの判定
            actual_loss = r.choice_loss if r.choice_loss is not None else 0
            if actual_loss == loss_res1:
                drawn_result = "状況 1"
            else:
                drawn_result = "状況 2"

            all_rounds.append({
                'round_num': r.round_number,
                'my_p': my_p,
                'other_p': other_p,
                'group_P': f"{calc_P * 100:.1f}%",
                'prob_result1': prob_res1,
                'prob_result2': prob_res2,
                'amount_result1': C.ENDOWMENT - loss_res1,
                'amount_result2': C.ENDOWMENT - loss_res2,
                'drawn_result': drawn_result,
                'round_payoff': int(r.round_payoff if r.round_payoff is not None else 0),
            })

        return {
            'selected_round': selected_round,
            'final_detail': final_detail,
            'final_payoff': int(player.participant.payoff),
            'all_rounds': all_rounds,
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
