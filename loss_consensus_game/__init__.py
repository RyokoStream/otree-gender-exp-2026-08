import random
from otree.api import *

doc = """
情報共有型くじ実験（両役体験練習付き・損失フレーム + Part1スライダーリスク）
"""

class C(BaseConstants):
    NAME_IN_URL = 'loss_consensus_game'
    PLAYERS_PER_GROUP = 2
    NUM_ROUNDS = 3

    # 初期所有（エンドウメント）と基準値
    ENDOWMENT = 1000
    BELIEF_ENDOWMENT = 100

    # ラウンドごとの結果1で選択肢Aが正解となる確率（%）
    PROBS_A_RESULT1 = {1: 60, 2: 70, 3: 80}


class Subsession(BaseSubsession):
    pass


def creating_session(subsession: Subsession):
    # ラウンド1の時点で、全4タスク（1: Part1, 2: 本番R1, 3: 本番R2, 4: 本番R3）から1つ決定
    if subsession.round_number == 1:
        for group in subsession.get_groups():
            # 1: Part 1, 2: 本番Round 1, 3: 本番Round 2, 4: 本番Round 3
            group.session.vars[f'selected_task_group_{group.id_in_subsession}'] = random.randint(1, 4)


class Group(BaseGroup):
    group_P = models.FloatField()


class Player(BasePlayer):
    student_id = models.StringField(
        label="もらっているID番号を入力してください。学籍番号を入力しないように:"
    )
    gender = models.StringField(
        label="戸籍上の性別を選択してください:",
        choices=['男性', '女性'],
        widget=widgets.RadioSelect
    )

    # --- Part 1: Slider Risk 用 ---
    slider_risk = models.IntegerField(
        label="スライダーを動かして数値を選択してください（0 〜 100）:",
        min=0, max=100
    )
    part1_payoff = models.FloatField(initial=0)

    # --- 練習ラウンド 1 用 ---
    practice_choice_1 = models.StringField(
        choices=['選択肢A', '選択肢B'],
        widget=widgets.RadioSelect,
        label="あなたの選択:"
    )
    practice_belief_1 = models.IntegerField(
        min=0, max=100,
        label="相手が「選択肢A」を選ぶ確率の予想 (0~100%):"
    )
    practice_payoff_1 = models.FloatField()

    # --- 練習ラウンド 2 用 ---
    practice_choice_2 = models.StringField(
        choices=['選択肢A', '選択肢B'],
        widget=widgets.RadioSelect,
        label="あなたの選択:"
    )
    practice_belief_2 = models.IntegerField(
        min=0, max=100,
        label="相手が「選択肢A」を選ぶ確率の予想 (0~100%):"
    )
    practice_payoff_2 = models.FloatField()

    # --- 本番ラウンド用 ---
    choice = models.StringField(
        choices=['選択肢A', '選択肢B'],
        widget=widgets.RadioSelect,
        label="あなたの選択:"
    )
    belief = models.IntegerField(
        min=0, max=100,
        label="相手が「選択肢A」を選ぶ確率の予想 (0~100%):"
    )

    # 計算結果保持用
    choice_loss = models.FloatField()
    belief_payoff = models.FloatField()
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


# --- Part 1: Slider Risk ---
class Part1SliderRisk(Page):
    form_model = 'player'
    form_fields = ['slider_risk']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        # Part 1 の利得計算ロジック（例: スライダー値 × 10）
        player.part1_payoff = player.slider_risk * 10.0


# --- 練習 1 ---
class Practice1(Page):
    form_model = 'player'
    form_fields = ['practice_choice_1', 'practice_belief_1']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class PracticeResults(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        dummy_p = 70.0
        dummy_other_choice = '選択肢A'
        
        # 練習1損失計算
        if player.practice_choice_1 == '選択肢A':
            p_loss = 1000.0 * (1.0 - dummy_p / 100.0)
        else:
            p_loss = 500.0

        actual_other_a = 100.0 if dummy_other_choice == '選択肢A' else 0.0
        b_payoff = C.BELIEF_ENDOWMENT - (actual_other_a - player.practice_belief_1) ** 2 / 100.0
        
        total_p_payoff = (C.ENDOWMENT - p_loss) + b_payoff
        player.practice_payoff_1 = total_p_payoff

        return {
            'dummy_p': dummy_p,
            'dummy_other_choice': dummy_other_choice,
            'p_loss': p_loss,
            'b_payoff': b_payoff,
            'total_payoff': total_p_payoff
        }


# --- 練習 2 ---
class Practice2(Page):
    form_model = 'player'
    form_fields = ['practice_choice_2', 'practice_belief_2']

    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1


class PracticeResults2(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        dummy_p = 40.0
        dummy_other_choice = '選択肢B'

        # 練習2損失計算
        if player.practice_choice_2 == '選択肢A':
            p_loss = 1000.0 * (1.0 - dummy_p / 100.0)
        else:
            p_loss = 500.0

        actual_other_a = 100.0 if dummy_other_choice == '選択肢A' else 0.0
        b_payoff = C.BELIEF_ENDOWMENT - (actual_other_a - player.practice_belief_2) ** 2 / 100.0
        
        total_p_payoff = (C.ENDOWMENT - p_loss) + b_payoff
        player.practice_payoff_2 = total_p_payoff

        return {
            'dummy_p': dummy_p,
            'dummy_other_choice': dummy_other_choice,
            'p_loss': p_loss,
            'b_payoff': b_payoff,
            'total_payoff': total_p_payoff
        }


# --- 本番意思決定 ---
class Decision(Page):
    form_model = 'player'
    form_fields = ['choice', 'belief']

    @staticmethod
    def vars_for_template(player: Player):
        round_num = player.round_number
        prob_A_res1 = C.PROBS_A_RESULT1.get(round_num, 50)
        return {
            'round_num': round_num,
            'prob_A_res1': prob_A_res1,
        }


# --- 成果集計・最終謝礼決定 ---
class ResultsWaitPage(WaitPage):
    @staticmethod
    def after_all_players_arrive(group: Group):
        players = group.get_players()
        
        # 1. グループの共通確率 P の決定（結果1: 確率PROBS_A_RESULT1, 結果2: 0%）
        round_num = group.round_number
        prob_res1 = C.PROBS_A_RESULT1.get(round_num, 50)
        
        # 50%の確率で結果1(P = prob_res1)、50%で結果2(P = 0)
        if random.random() < 0.5:
            group.group_P = float(prob_res1)
        else:
            group.group_P = 0.0

        # 2. 各プレイヤーの利得計算（損失フレーム）
        p1 = players[0]
        p2 = players[1]

        for p, other in [(p1, p2), (p2, p1)]:
            # 意思決定の損失計算
            if p.choice == '選択肢A':
                p.choice_loss = 1000.0 * (1.0 - group.group_P / 100.0)
            else:
                p.choice_loss = 500.0

            # 信念当て報酬計算（相手の選択との誤差）
            actual_other_a = 100.0 if other.choice == '選択肢A' else 0.0
            p.belief_payoff = C.BELIEF_ENDOWMENT - ((actual_other_a - p.belief) ** 2) / 100.0

            # 今ラウンドの利得 = (1000 - 損失) + 信念当て報酬
            p.round_payoff = (C.ENDOWMENT - p.choice_loss) + p.belief_payoff

        # 3. 最終ラウンド完了時に4つのタスクからランダムで1つ決定
        if group.round_number == C.NUM_ROUNDS:
            selected_task = group.session.vars.get(
                f'selected_task_group_{group.id_in_subsession}',
                random.randint(1, 4)
            )

            for p in players:
                p.participant.vars['selected_task'] = selected_task
                
                if selected_task == 1:
                    # Part 1（ラウンド1のレコードから取得）
                    p1_player = p.in_round(1)
                    p.participant.payoff = p1_player.part1_payoff
                else:
                    # 本番ラウンド（2 -> Round 1, 3 -> Round 2, 4 -> Round 3）
                    actual_round = selected_task - 1
                    selected_player = p.in_round(actual_round)
                    p.participant.payoff = selected_player.round_payoff


class FinalResults(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        all_rounds_data = []
        for r in range(1, C.NUM_ROUNDS + 1):
            pr = player.in_round(r)
            all_rounds_data.append({
                'round': r,
                'choice': pr.choice,
                'belief': pr.belief,
                'choice_loss': pr.choice_loss,
                'belief_payoff': pr.belief_payoff,
                'payoff': pr.round_payoff,
            })

        selected_task = player.participant.vars.get('selected_task', 1)

        return {
            'all_rounds': all_rounds_data,
            'selected_task': selected_task,  # 1ならPart1、2〜4なら本番各ラウンド
            'final_payoff': int(player.participant.payoff),
            'part1_payoff': player.in_round(1).part1_payoff,
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
