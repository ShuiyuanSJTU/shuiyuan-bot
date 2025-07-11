from typing import Optional

from .base_bot_report_action import BaseBotReportAction
from .bot_action_annual_interaction_report import BotInteractionReport
from .bot_action_annual_post_report import BotPostReport
from .bot_action_annual_read_report import BotReadReport

from ...bot_manager import bot_manager as BotManager


class BotSummaryReport(BaseBotReportAction):
    action_name = "BotSummaryReport"
    trigger_keyword = "我的2024报告"

    def __init__(self) -> None:
        super().__init__()
        self.action_cached = False
        self.interaction_report: Optional[BotInteractionReport] = None
        self.post_report: Optional[BotPostReport] = None
        self.read_report: Optional[BotReadReport] = None

    def _lookup_actions(self):
        if not self.action_cached:
            activated_actions = BotManager.activated_actions
            self.interaction_report = activated_actions.get(
                BotInteractionReport.action_name)
            self.post_report = activated_actions.get(BotPostReport.action_name)
            self.read_report = activated_actions.get(BotReadReport.action_name)
            self.action_cached = True

    # do not cache this function
    def get_reply_main_content(self, user_id, post_data, opts):
        self._lookup_actions()
        action_response = []
        try:
            action_response.append(self.read_report.get_reply_main_content(
                user_id, post_data, opts))
        except Exception:
            pass

        try:
            action_response.append(self.post_report.get_reply_main_content(
                user_id, post_data, opts))
        except Exception:
            pass

        try:
            action_response.append(self.interaction_report.get_reply_main_content(
                user_id, post_data, opts))
        except Exception:
            pass

        raw = "\n\n".join(action_response)
        return raw
