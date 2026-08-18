class ResultsWaitPage(WaitPage):
    title_text = "集計中"
    body_text = "ペアの入力完了を待っています..."

    @staticmethod
    def after_all_players_arrive(group: Group):
        players = group.get_players()
        avg_p_int = sum([p.p_input for p in players]) / len(players)
        group.group_P = round(avg_p_int / 100.0, 4)

        P = group.group_P
        r_num = group.round_number
        prob_a_threshold = C.PROBS_A_RESULT1[r_num] / 100.0

        for p in players:
            is_player_a = (p.id_in_group == 1)
            prob_res1_threshold = prob_a_threshold if is_player_a else (1.0 - prob_a_threshold)

            # 状況抽選
            if random.random() < prob_res1_threshold:
                p.drawn_result = "状況 1"
                # 状況1が発生したときの手元残金
                payoff_val = (P * 2000) if is_player_a else ((1 - P) * 2000)
            else:
                p.drawn_result = "状況 2"
                # 状況2が発生したときの手元残金
                payoff_val = ((1 - P) * 2000) if is_player_a else (P * 2000)

            p.round_payoff = round(payoff_val)
            p.payoff = p.round_payoff

        # 最終ラウンドで支払確定額を設定
        if group.round_number == C.NUM_ROUNDS:
            selected_round = group.session.vars.get(
                f'selected_round_group_{group.id_in_subsession}',
                random.randint(1, C.NUM_ROUNDS)
            )
            for p in players:
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

            # 役割ごとの各状況の残金額と損失額の計算
            if is_player_a:
                amt_res1 = round(group_P * 2000)
                amt_res2 = round((1 - group_P) * 2000)
            else:
                amt_res1 = round((1 - group_P) * 2000)
                amt_res2 = round(group_P * 2000)

            loss_res1 = 2000 - amt_res1
            loss_res2 = 2000 - amt_res2
            round_loss = 2000 - int(p.round_payoff)

            all_rounds_data.append({
                'round_num': r_num,
                'my_p': p.p_input,
                'other_p': other_p.p_input,
                'group_P': group_P,
                'prob_result1': prob_result1,
                'prob_result2': prob_result2,
                'amount_result1': amt_res1,
                'amount_result2': amt_res2,
                'loss_result1': loss_res1,
                'loss_result2': loss_res2,
                'drawn_result': p.drawn_result,
                'round_payoff': int(p.round_payoff),
                'round_loss': round_loss,
            })

        selected_round = player.participant.vars.get('selected_round', 1)

        return {
            'all_rounds': all_rounds_data,
            'selected_round': selected_round,
            'role_name': role_name,
            'final_payoff': int(player.participant.payoff),
        }
