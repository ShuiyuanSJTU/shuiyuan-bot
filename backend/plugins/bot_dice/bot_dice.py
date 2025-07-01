from ...bot_action import BotAction, on
from ...model.post import Post
import re
import numpy as np


class ParamError(ValueError):
    pass


class UnsupportedDistributionError(ValueError):
    pass


class ParseError(ValueError):
    pass


class BotDice(BotAction):
    action_name = "BotDice"

    @staticmethod
    def help_message():
        help_text = """
投掷 投掷次数+d+分布及参数，例如

> 投掷 2dN(0,1)

支持的分布类型及其参数说明:
1. 正态分布 (N): $N(\\mu, \\sigma^2)$
- 概率密度函数: $f(x|\\mu,\\sigma^2) = \\frac{1}{\\sqrt{2\\pi\\sigma^2}}e^{-\\frac{(x-\\mu)^2}{2\\sigma^2}}$
- 参数: 均值($\\mu$), 标准差($\\sigma$)
2. 均匀分布 (U): $U(a, b)$
- 概率密度函数: $f(x|a,b) = \\frac{1}{b-a}$, 对于 $a \\leq x \\leq b$
- 参数: 最小值($a$), 最大值($b$)
3. 二项分布 (B): $B(n, p)$
- 概率质量函数: $f(k|n,p) = \\binom{n}{k}p^k(1-p)^{n-k}$
- 参数: 试验次数($n$), 成功概率($p$)
4. 泊松分布 (Pois): $Pois(\\lambda)$
- 概率质量函数: $f(k|\\lambda) = \\frac{\\lambda^k e^{-\\lambda}}{k!}$
- 参数: 平均发生率($\\lambda$)
5. 指数分布 (Exp): $Exp(\\lambda)$
- 概率密度函数: $f(x|\\lambda) = \\lambda e^{-\\lambda x}$, 对于 $x \\geq 0$
- 参数: $\\lambda$
6. 伽马分布 (Gamma): $\\Gamma(k, \\theta)$
- 概率密度函数: $f(x|k,\\theta) = \\frac{x^{k-1}e^{-\\frac{x}{\\theta}}}{\\theta^k\\Gamma(k)}$, 对于 $x > 0$
- 参数: 形状参数($k$), 尺度参数($\\theta$)
7. 贝塔分布 (Beta): $Beta(\\alpha, \\beta)$
- 概率密度函数: $f(x|\\alpha,\\beta) = \\frac{x^{\\alpha-1}(1-x)^{\\beta-1}}{B(\\alpha,\\beta)}$, 对于 $0 < x < 1$
- 参数: $\\alpha$, $\\beta$
8. 几何分布 (Geom): $Geom(p)$
- 概率质量函数: $f(k|p) = (1-p)^{k-1}p$, 对于 $k = 1, 2, ...$
- 参数: 成功概率($p$)
"""
        return help_text

    @staticmethod
    def parse_and_generate_basic_random_numbers(input_str):
        match = re.search(r"投掷 (\d+)d(\d+)", input_str)
        if not match:
            raise ParseError("无法解析输入。")

        times, sides = match.groups()
        if not times.isdigit() or not sides.isdigit():
            raise ParseError("投掷次数和面数必须是正整数。")
        if int(times) > 100:
            raise ParamError("投掷次数不能超过100次。")

        times = int(times)
        sides = int(sides)
        numbers = np.random.randint(1, sides+1, times)
        return numbers

    @staticmethod
    def parse_and_generate_advanced_random_numbers(input_str):
        match = re.search(r"投掷 (\d+)d([A-Za-z]+)\((.*?)\)", input_str)
        if not match:
            raise ParseError("无法解析输入。")

        times, dist_type, params = match.groups()
        if not times.isdigit():
            raise ParseError("投掷次数必须是正整数。")
        if int(times) > 20:
            raise ParamError("投掷次数不能超过100次。")
        times = int(times)
        params = [float(x) for x in params.split(',')]

        if dist_type == "N":
            if len(params) != 2:
                raise ParamError("正态分布需要2个参数：均值和标准差。")
            numbers = np.random.normal(params[0], params[1], times)
        elif dist_type == "U":
            if len(params) != 2:
                raise ParamError("均匀分布需要2个参数：最小值和最大值。")
            numbers = np.random.uniform(params[0], params[1], times)
        elif dist_type == "B":
            if len(params) != 2:
                raise ParamError("二项分布需要2个参数：试验次数和成功概率。")
            numbers = np.random.binomial(int(params[0]), params[1], times)
        elif dist_type == "Pois":
            if len(params) != 1:
                raise ParamError("泊松分布需要1个参数：平均发生率。")
            numbers = np.random.poisson(params[0], times)
        elif dist_type == "Exp":
            if len(params) != 1:
                raise ParamError("指数分布需要1个参数：率参数（lambda）。")
            numbers = np.random.exponential(1/params[0], times)
        elif dist_type == "Gamma":
            if len(params) != 2:
                raise ParamError("伽马分布需要2个参数：形状参数（k）和尺度参数（theta）。")
            numbers = np.random.gamma(params[0], params[1], times)
        elif dist_type == "Beta":
            if len(params) != 2:
                raise ParamError("贝塔分布需要2个参数：形状参数alpha和beta。")
            numbers = np.random.beta(params[0], params[1], times)
        elif dist_type == "Geom":
            if len(params) != 1:
                raise ParamError("几何分布需要1个参数：成功概率p。")
            numbers = np.random.geometric(params[0], times)
        else:
            raise UnsupportedDistributionError("不支持的分布类型。")

        return numbers

    @staticmethod
    def result_numbers_to_str(result_numbers: np.ndarray, advanced=False, int_only=False):
        if not advanced:
            return ", ".join(map(str, result_numbers))
        if int_only:
            return ", ".join(map(str, np.round(result_numbers).astype(int)))
        else:
            return ", ".join(map(lambda x: f"{x:.2f}", result_numbers))

    def get_reply(self, post: Post):
        advanced = bool(re.search(r"投掷 (\d+)d([A-Za-z]+)\((.*?)\)", post.raw))
        int_only = "取整" in post.raw
        reply_text = ""
        result_numbers = None
        try:
            if not advanced:
                result_numbers = self.parse_and_generate_basic_random_numbers(
                    post.raw)
            else:
                result_numbers = self.parse_and_generate_advanced_random_numbers(
                    post.raw)
        except (ParamError, UnsupportedDistributionError, ParseError) as e:
            reply_text = f"错误：{str(e)}\n 使用 '投掷 帮助' 查看帮助。"
        except ValueError:
            reply_text = "错误：数值错误。"
        except Exception as e:
            reply_text = "错误：未知错误。"
            print(e)

        if result_numbers is not None:
            reply_text = f"> {self.result_numbers_to_str(result_numbers, advanced, int_only)}"

        return reply_text

    def should_response(self, post: Post):
        return super().should_response(post) and "投掷" in post.raw

    @on("post_created")
    def on_post_created(self, post: Post):
        if not self.should_response(post):
            return False

        if "投掷 帮助" in post.raw:
            reply_text = self.help_message()
        else:
            reply_text = self.get_reply(post)

        self.api.create_post(reply_text, post.topic_id,
                             post.post_number, skip_validations=True)

        return True
