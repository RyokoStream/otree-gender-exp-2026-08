import json
from otree.api import Bot, Submission
from . import Introduction, Practice, Transition, FinalStep1, FinalStep2, C


class PlayerBot(Bot):
    def play_round(self):
        yield Submission(Introduction, {})

        practice_history = [
            {
                'count': i + 1,
                'zone': f'{0.1 * i:.2f}',
                'result': '空振り三振！' if i % 2 == 0 else 'ホームラン！',
                'isStrike': i % 2 == 0,
            }
            for i in range(C.NUM_PRACTICE_PITCHES)
        ]
        yield Submission(
            Practice,
            {'practice_data': json.dumps(practice_history)},
        )

        yield Submission(Transition, {})

        yield Submission(FinalStep1, {'ideal_zone': 0.35})

        yield Submission(FinalStep2, {'sign_q': 0.2})

        assert self.player.actual_zone == (C.CATCHER_ZONE + 0.2) / 2
        assert self.player.reward is not None
        assert '獲得報酬' in self.html
        assert str(self.player.reward) in self.html
