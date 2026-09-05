"""Savollarni (misollarni) generatsiya qilish — arifmetika va kasrlar.

Har bir savol lug'at (dict) shaklida qaytadi:
    {"a", "b", "c", "d", "operation", "answer", "choices"}
`a`/`b`/`c`/`d` — sonlar (kasrlarda: a/b — birinchi kasr, c/d — ikkinchi
kasr; ba'zi amallarda faqat a/b ishlatiladi, c/d = None). `answer` va
`choices` — HAR DOIM matn (string) sifatida qaytariladi (masalan "108",
"3/4", "2 3/4", "0.75", "<"), shunda arifmetika va kasrlar bir xil
qatorda (baza ustunlari TEXT) saqlanishi mumkin.
"""
import math
import random
from fractions import Fraction

ARITHMETIC_OPS = {
    "add", "sub", "mul", "div", "compare",
    "arith_order", "arith_remainder", "arith_negative",
}
FRACTION_OPS = {
    "frac_compare", "frac_simplify", "frac_add", "frac_sub",
    "frac_mul", "frac_div", "frac_mixed", "frac_decimal", "frac_basic",
}
PERCENT_OPS = {
    "percent_of", "percent_find_whole", "percent_increase",
    "percent_discount", "percent_profit_loss", "percent_successive",
}
ALGEBRA_OPS = {
    "algebra_equation", "algebra_inequality", "algebra_expand",
    "algebra_simplify", "algebra_exponent", "algebra_root", "algebra_system",
}
GEOMETRY_OPS = {
    "geo_perimeter", "geo_area", "geo_volume", "geo_triangle",
    "geo_quad", "geo_circle", "geo_pythagoras", "geo_angles",
}
FUNCTION_OPS = {
    "func_linear", "func_quadratic", "func_graph", "func_value", "func_zeros",
}
STATISTICS_OPS = {
    "stat_mean", "stat_median", "stat_mode", "stat_probability", "stat_combinatorics",
}


# ============================================================
# ARIFMETIKA (qo'shish / ayirish / ko'paytirish / bo'lish / solishtirish)
# ============================================================

def _rand_n_digit(digits: int) -> int:
    """digits xonali tasodifiy musbat son qaytaradi (masalan 2 xonali: 10-99)."""
    if digits <= 0:
        return 0
    low = 10 ** (digits - 1) if digits > 1 else 0
    high = 10 ** digits - 1
    return random.randint(low, high)


def _generate_arith_pair(operation: str, digits: int):
    """operation va digits asosida (a, b, javob:int-yoki-str) qaytaradi."""
    if operation == "add":
        a = _rand_n_digit(digits)
        b = _rand_n_digit(digits)
        return a, b, a + b

    if operation == "sub":
        # natija manfiy bo'lmasligi uchun a >= b
        a = _rand_n_digit(digits)
        b = random.randint(0, a)
        return a, b, a - b

    if operation == "mul":
        # ko'paytirish uchun ikkala son ham digits xonali bo'lsa natija juda
        # katta bo'lib ketmasligi uchun ikkinchi ko'paytuvchini kichikroq olamiz
        a = _rand_n_digit(digits)
        b_digits = digits if digits <= 2 else max(1, digits - 1)
        b = _rand_n_digit(b_digits)
        return a, b, a * b

    if operation == "div":
        # bo'linma butun son bo'lishi uchun avval bo'luvchi va natijani tanlaymiz
        divisor = _rand_n_digit(digits)
        if divisor == 0:
            divisor = 1
        quotient_digits = digits if digits <= 2 else max(1, digits - 1)
        quotient = _rand_n_digit(quotient_digits)
        if quotient == 0:
            quotient = 1
        dividend = divisor * quotient
        return dividend, divisor, quotient

    if operation == "compare":
        a = _rand_n_digit(digits)
        # ba'zida ikkala son teng bo'lsin ("=" varianti ham chiqishi uchun)
        b = a if random.random() < 0.15 else _rand_n_digit(digits)
        if a < b:
            answer = "<"
        elif a > b:
            answer = ">"
        else:
            answer = "="
        return a, b, answer

    raise ValueError(f"Noma'lum amal: {operation}")


def _make_int_distractors(correct: int, count: int = 3) -> list[int]:
    """To'g'ri javobga yaqin, lekin undan farqli 'yolg'on' variantlar yaratadi."""
    distractors: set[int] = set()
    attempts = 0
    max_delta = max(3, abs(correct) // 10 + 5)
    while len(distractors) < count and attempts < 100:
        attempts += 1
        delta = random.randint(-max_delta, max_delta)
        if delta == 0:
            continue
        candidate = correct + delta
        if candidate < 0:
            candidate = correct + abs(delta)
        if candidate == correct or candidate in distractors:
            continue
        distractors.add(candidate)
    # agar yetarli noyob variant topilmasa, oddiy siljish bilan to'ldiramiz
    filler = 1
    while len(distractors) < count:
        candidate = correct + filler
        if candidate != correct and candidate not in distractors and candidate >= 0:
            distractors.add(candidate)
        filler += 1
    return list(distractors)[:count]


def _generate_arithmetic_question(operation: str, digits: int) -> dict:
    a, b, answer = _generate_arith_pair(operation, digits)
    if operation == "compare":
        choices = ["<", ">", "="]
        random.shuffle(choices)
        answer_str = answer
    else:
        choices = [str(x) for x in _make_int_distractors(answer, 3)] + [str(answer)]
        random.shuffle(choices)
        answer_str = str(answer)
    return {
        "a": a, "b": b, "c": None, "d": None,
        "operation": operation,
        "answer": answer_str,
        "choices": choices,
    }


# ---------- Amal tartibi / qoldiqli bo'lish / manfiy sonlar ----------

_ORDER_RANGE = {1: 10, 2: 12, 3: 15, 4: 20, 5: 25}


def _arith_order(level: int) -> dict:
    rng = _ORDER_RANGE.get(level, 15)
    template = min(level, 5)
    if template == 1:
        a, b, c = random.randint(1, rng), random.randint(1, rng), random.randint(1, rng)
        display_text = f"{a} + {b} × {c}"
        answer = a + b * c
    elif template == 2:
        a, b = random.randint(2, rng), random.randint(2, rng)
        c = random.randint(1, a * b - 1) if a * b > 1 else 1
        display_text = f"{a} × {b} - {c}"
        answer = a * b - c
    elif template == 3:
        a, b, c = random.randint(1, rng), random.randint(1, rng), random.randint(2, 9)
        display_text = f"({a} + {b}) × {c}"
        answer = (a + b) * c
    elif template == 4:
        a = random.randint(2, 9)
        b = random.randint(2, rng)
        c = random.randint(1, b - 1)
        d = random.randint(1, rng)
        display_text = f"{a} × ({b} - {c}) + {d}"
        answer = a * (b - c) + d
    else:
        a, b = random.randint(1, rng), random.randint(1, rng)
        c = random.randint(2, rng)
        d = random.randint(1, c - 1)
        display_text = f"({a} + {b}) × ({c} - {d})"
        answer = (a + b) * (c - d)

    choices = [str(v) for v in _general_int_distractors(answer, 3)] + [str(answer)]
    random.shuffle(choices)
    return {
        "a": None, "b": None, "c": None, "d": None,
        "operation": "arith_order", "answer": str(answer), "choices": choices,
        "display_text": display_text,
    }


_REMAINDER_RANGE = {1: (2, 6), 2: (2, 8), 3: (3, 10), 4: (3, 12), 5: (4, 15)}


def _remainder_distractors(quotient: int, remainder: int, divisor: int, count: int = 3) -> list[str]:
    correct = f"{quotient} qoldiq {remainder}"
    seen = {correct}
    out: list[str] = []
    candidates = [
        (quotient + 1, remainder), (max(0, quotient - 1), remainder),
        (quotient, (remainder + 1) % divisor), (quotient, max(1, remainder - 1)),
        (quotient + 1, max(1, remainder - 1)), (max(0, quotient - 1), remainder),
    ]
    random.shuffle(candidates)
    for q, r in candidates:
        if r <= 0 or r >= divisor or len(out) >= count:
            continue
        s = f"{q} qoldiq {r}"
        if s not in seen:
            seen.add(s)
            out.append(s)
    filler = 1
    while len(out) < count:
        s = f"{quotient + filler} qoldiq {remainder}"
        if s not in seen:
            seen.add(s)
            out.append(s)
        filler += 1
    return out[:count]


def _arith_remainder(level: int) -> dict:
    lo, hi = _REMAINDER_RANGE.get(level, (2, 10))
    divisor = random.randint(lo, hi)
    quotient = random.randint(2, 5 + level * 2)
    remainder = random.randint(1, divisor - 1)
    dividend = divisor * quotient + remainder
    answer = f"{quotient} qoldiq {remainder}"
    choices = _remainder_distractors(quotient, remainder, divisor, 3) + [answer]
    random.shuffle(choices)
    return {
        "a": dividend, "b": divisor, "c": None, "d": None,
        "operation": "arith_remainder", "answer": answer, "choices": choices,
    }


_NEG_RANGE = {1: 10, 2: 15, 3: 20, 4: 30, 5: 50}


def _fmt_signed_operand(n: int) -> str:
    return f"({n})" if n < 0 else str(n)


def _arith_negative(level: int) -> dict:
    rng = _NEG_RANGE.get(level, 20)
    op = random.choice(["add", "sub", "mul", "div"])
    if op == "div":
        divisor = random.randint(1, max(2, rng // 2)) * random.choice([1, -1])
        if divisor == 0:
            divisor = 1
        quotient = random.randint(1, max(2, rng // 2)) * random.choice([1, -1])
        a = divisor * quotient
        b = divisor
        answer = quotient
        symbol = "÷"
    else:
        a = random.randint(-rng, rng)
        b = random.randint(-rng, rng)
        if op == "add":
            answer, symbol = a + b, "+"
        elif op == "sub":
            answer, symbol = a - b, "-"
        else:
            answer, symbol = a * b, "×"

    display_text = f"{_fmt_signed_operand(a)} {symbol} {_fmt_signed_operand(b)}"
    choices = [str(v) for v in _general_int_distractors(answer, 3)] + [str(answer)]
    random.shuffle(choices)
    return {
        "a": None, "b": None, "c": None, "d": None,
        "operation": "arith_negative", "answer": str(answer), "choices": choices,
        "display_text": display_text,
    }


# ============================================================
# KASRLAR
# ============================================================

# "digits" (1-5) kasrlarda "murakkablik darajasi" sifatida ishlatiladi —
# daraja qancha katta bo'lsa, maxrajlar shuncha katta bo'ladi.
_FRACTION_MAX_DEN = {1: 6, 2: 8, 3: 12, 4: 16, 5: 20}
_FRACTION_DECIMAL_DENOMS = {
    1: [2, 4, 5, 10],
    2: [2, 4, 5, 8, 10, 20],
    3: [2, 4, 5, 8, 10, 20, 25],
    4: [2, 4, 5, 8, 10, 20, 25, 40, 50],
    5: [2, 4, 5, 8, 10, 16, 20, 25, 40, 50, 100],
}


def _frac_str(n: int, d: int) -> str:
    f = Fraction(n, d)
    if f.denominator == 1:
        return str(f.numerator)
    return f"{f.numerator}/{f.denominator}"


def _fmt_mixed(n: int, d: int) -> str:
    """Noto'g'ri kasrni (n/d, n>d bo'lishi shart emas) aralash songa aylantiradi."""
    f = Fraction(n, d)
    whole, rem = divmod(f.numerator, f.denominator)
    if rem == 0:
        return str(whole)
    if whole == 0:
        return f"{rem}/{f.denominator}"
    return f"{whole} {rem}/{f.denominator}"


def _fmt_decimal(n: int, d: int) -> str:
    """n/d ni aniq (moslashtirilgan) o'nli kasr satriga aylantiradi."""
    for places in range(0, 6):
        scaled = n * (10 ** places)
        if scaled % d == 0:
            val = scaled // d
            if places == 0:
                return str(val)
            s = str(val).zfill(places + 1)
            return f"{s[:-places]}.{s[-places:]}"
    # kafolatlangan bo'lmasa (kutilmagan holat), taxminiy qiymat
    return f"{n / d:.4f}".rstrip("0").rstrip(".")


def _rand_proper_fraction(level: int) -> Fraction:
    max_den = _FRACTION_MAX_DEN.get(level, 12)
    den = random.randint(2, max_den)
    num = random.randint(1, den - 1)
    return Fraction(num, den)


def _frac_distractors(correct: Fraction, count: int = 3) -> list[str]:
    """To'g'ri kasrga yaqin, lekin undan farqli noto'g'ri variantlar yaratadi."""
    correct_str = _frac_str(correct.numerator, correct.denominator)
    seen = {correct_str}
    out: list[str] = []
    attempts = 0
    while len(out) < count and attempts < 80:
        attempts += 1
        dn = random.choice([-2, -1, 1, 2])
        dd = random.choice([-2, -1, 0, 0, 1, 2])
        num = correct.numerator + dn
        den = correct.denominator + dd
        if den <= 0 or num <= 0:
            continue
        s = _frac_str(num, den)
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    filler = 1
    while len(out) < count:
        cand = correct + filler
        s = _frac_str(cand.numerator, cand.denominator)
        if s not in seen:
            seen.add(s)
            out.append(s)
        filler += 1
    return out[:count]


def _mixed_distractors(whole: int, rem: int, den: int, count: int = 3) -> list[str]:
    correct_str = _fmt_mixed(whole * den + rem, den)
    seen = {correct_str}
    out: list[str] = []
    candidates = [
        (whole + 1, rem, den),
        (max(0, whole - 1), rem, den),
        (whole, min(den - 1, rem + 1), den),
        (whole, max(1, rem - 1), den),
        (whole + 1, max(1, rem - 1), den),
    ]
    random.shuffle(candidates)
    for w, r, d in candidates:
        if len(out) >= count:
            break
        s = _fmt_mixed(w * d + r, d)
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    filler = 2
    while len(out) < count:
        s = _fmt_mixed((whole + filler) * den + rem, den)
        if s not in seen:
            seen.add(s)
            out.append(s)
        filler += 1
    return out[:count]


def _decimal_distractors(n: int, d: int, correct_str: str, count: int = 3) -> list[str]:
    places = len(correct_str.split(".")[1]) if "." in correct_str else 0
    scale = 10 ** places
    correct_scaled = round(n * scale / d)
    seen = {correct_str}
    out: list[str] = []
    deltas = [1, -1, 2, -2, 5, -5, 10, -10]
    random.shuffle(deltas)
    for delta in deltas:
        if len(out) >= count:
            break
        val = correct_scaled + delta
        if val <= 0:
            continue
        s = f"{val / scale:.{places}f}" if places > 0 else str(val)
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    filler = 1
    while len(out) < count:
        val = correct_scaled + 20 + filler
        s = f"{val / scale:.{places}f}" if places > 0 else str(val)
        if s not in seen:
            seen.add(s)
            out.append(s)
        filler += 1
    return out[:count]


def _generate_fraction_question(operation: str, level: int) -> dict:
    if operation == "frac_compare":
        f1 = _rand_proper_fraction(level)
        if random.random() < 0.2:
            k = random.randint(2, 4)
            f2 = Fraction(f1.numerator * k, f1.denominator * k)
        else:
            f2 = _rand_proper_fraction(level)
        if f1 < f2:
            answer = "<"
        elif f1 > f2:
            answer = ">"
        else:
            answer = "="
        choices = ["<", ">", "="]
        random.shuffle(choices)
        return {
            "a": f1.numerator, "b": f1.denominator,
            "c": f2.numerator, "d": f2.denominator,
            "operation": operation, "answer": answer, "choices": choices,
        }

    if operation == "frac_simplify":
        max_den = _FRACTION_MAX_DEN.get(level, 12)
        for _ in range(200):
            den = random.randint(4, max_den * 2)
            num = random.randint(2, den - 1)
            if math.gcd(num, den) > 1:
                break
        else:
            num, den = 4, 8
        simplified = Fraction(num, den)
        answer = _frac_str(simplified.numerator, simplified.denominator)
        choices = _frac_distractors(simplified, 3) + [answer]
        random.shuffle(choices)
        return {
            "a": num, "b": den, "c": None, "d": None,
            "operation": operation, "answer": answer, "choices": choices,
        }

    if operation in ("frac_add", "frac_sub", "frac_mul", "frac_div"):
        f1 = _rand_proper_fraction(level)
        f2 = _rand_proper_fraction(level)
        if operation == "frac_sub" and f1 < f2:
            f1, f2 = f2, f1
        if operation == "frac_div":
            attempts = 0
            while f2.numerator == 0 and attempts < 10:
                f2 = _rand_proper_fraction(level)
                attempts += 1
        result = {
            "frac_add": f1 + f2,
            "frac_sub": f1 - f2,
            "frac_mul": f1 * f2,
            "frac_div": f1 / f2 if f2 != 0 else f1,
        }[operation]
        answer = _frac_str(result.numerator, result.denominator)
        choices = _frac_distractors(result, 3) + [answer]
        random.shuffle(choices)
        return {
            "a": f1.numerator, "b": f1.denominator,
            "c": f2.numerator, "d": f2.denominator,
            "operation": operation, "answer": answer, "choices": choices,
        }

    if operation == "frac_mixed":
        max_den = _FRACTION_MAX_DEN.get(level, 12)
        den = random.randint(2, max_den)
        whole = random.randint(1, min(9, level + 2))
        rem = random.randint(1, den - 1)
        num = whole * den + rem
        answer = _fmt_mixed(num, den)
        choices = _mixed_distractors(whole, rem, den, 3) + [answer]
        random.shuffle(choices)
        return {
            "a": num, "b": den, "c": None, "d": None,
            "operation": operation, "answer": answer, "choices": choices,
        }

    if operation == "frac_decimal":
        denoms = _FRACTION_DECIMAL_DENOMS.get(level, [2, 4, 5, 10])
        den = random.choice(denoms)
        num = random.randint(1, den - 1)
        answer = _fmt_decimal(num, den)
        choices = _decimal_distractors(num, den, answer, 3) + [answer]
        random.shuffle(choices)
        return {
            "a": num, "b": den, "c": None, "d": None,
            "operation": operation, "answer": answer, "choices": choices,
        }

    if operation == "frac_basic":
        return _frac_basic(level)

    raise ValueError(f"Noma'lum kasr amali: {operation}")


def _frac_basic_distractors(n: int, d: int, count: int = 3) -> list[str]:
    """frac_basic uchun — n/d ni QISQARTIRMASDAN (o'qilgan holicha)
    distraktorlar yaratadi."""
    correct = f"{n}/{d}"
    seen = {correct}
    out: list[str] = []
    candidates = [
        (n + 1, d), (max(1, n - 1), d), (n, d + 1),
        (n, max(n + 1, d - 1)), (d - n, d), (n + 1, d + 1),
    ]
    random.shuffle(candidates)
    for nn, dd in candidates:
        if dd < 2 or nn < 1 or nn >= dd or len(out) >= count:
            continue
        s = f"{nn}/{dd}"
        if s not in seen:
            seen.add(s)
            out.append(s)
    filler = 1
    while len(out) < count:
        dd = d + filler + 1
        if n < dd:
            s = f"{n}/{dd}"
            if s not in seen:
                seen.add(s)
                out.append(s)
        filler += 1
    return out[:count]


def _frac_basic(level: int) -> dict:
    max_den = _FRACTION_MAX_DEN.get(level, 12)
    d = random.randint(2, max_den)
    n = random.randint(1, d - 1)
    answer = f"{n}/{d}"
    choices = _frac_basic_distractors(n, d, 3) + [answer]
    random.shuffle(choices)
    return {
        "a": n, "b": d, "c": None, "d": None,
        "operation": "frac_basic", "answer": answer, "choices": choices,
    }


# ============================================================
# FOIZLAR
# ============================================================

# "digits" (1-5) foizlarda ham "murakkablik darajasi" sifatida ishlatiladi —
# daraja qancha katta bo'lsa, sonlar shuncha katta bo'ladi.
_PERCENTS = [5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 75, 80, 90]
_PERCENT_BASE_MAX_MULT = {1: 10, 2: 20, 3: 40, 4: 80, 5: 150}
_PERCENT_ROUND_STEP = {1: 10, 2: 10, 3: 50, 4: 50, 5: 100}
_PERCENT_ROUND_MAX_MULT = {1: 20, 2: 40, 3: 40, 4: 60, 5: 80}


def _rand_percent() -> int:
    return random.choice(_PERCENTS)


def _base_for_percent(p: int, level: int) -> int:
    """p% ni butun songa aylantirish uchun kerakli ko'paytmaga ega son."""
    g = math.gcd(p, 100)
    unit = 100 // g
    max_mult = _PERCENT_BASE_MAX_MULT.get(level, 40)
    mult = random.randint(1, max_mult)
    base = unit * mult
    return base if base > 0 else unit


def _rand_round_base(level: int) -> int:
    step = _PERCENT_ROUND_STEP.get(level, 10)
    max_mult = _PERCENT_ROUND_MAX_MULT.get(level, 40)
    return step * random.randint(1, max_mult)


def _generate_percent_question(operation: str, level: int) -> dict:
    if operation == "percent_of":
        p = _rand_percent()
        n = _base_for_percent(p, level)
        answer = p * n // 100
        choices = [str(x) for x in _make_int_distractors(answer, 3)] + [str(answer)]
        random.shuffle(choices)
        return {"a": n, "b": p, "c": None, "d": None, "operation": operation,
                "answer": str(answer), "choices": choices}

    if operation == "percent_find_whole":
        p = _rand_percent()
        x = _base_for_percent(p, level)
        value = p * x // 100
        answer = x
        choices = [str(v) for v in _make_int_distractors(answer, 3)] + [str(answer)]
        random.shuffle(choices)
        return {"a": value, "b": p, "c": None, "d": None, "operation": operation,
                "answer": str(answer), "choices": choices}

    if operation == "percent_increase":
        p = _rand_percent()
        n = _base_for_percent(p, level)
        answer = n + (p * n // 100)
        choices = [str(v) for v in _make_int_distractors(answer, 3)] + [str(answer)]
        random.shuffle(choices)
        return {"a": n, "b": p, "c": None, "d": None, "operation": operation,
                "answer": str(answer), "choices": choices}

    if operation == "percent_discount":
        p = _rand_percent()
        n = _base_for_percent(p, level)
        answer = n - (p * n // 100)
        choices = [str(v) for v in _make_int_distractors(answer, 3)] + [str(answer)]
        random.shuffle(choices)
        return {"a": n, "b": p, "c": None, "d": None, "operation": operation,
                "answer": str(answer), "choices": choices}

    if operation == "percent_profit_loss":
        p = _rand_percent()
        cost = _base_for_percent(p, level)
        is_profit = random.random() < 0.5
        sell = cost + (p * cost // 100) if is_profit else cost - (p * cost // 100)
        label = "foyda" if is_profit else "zarar"
        opposite = "zarar" if is_profit else "foyda"
        answer = f"{p}% {label}"
        distractor_pcts = _make_int_distractors(p, 2)
        choices = {answer, f"{p}% {opposite}"}
        for dp in distractor_pcts:
            choices.add(f"{max(1, dp)}% {label}")
        filler = 1
        while len(choices) < 4:
            choices.add(f"{p + filler}% {label}")
            filler += 1
        choices = list(choices)[:4]
        if answer not in choices:
            choices[-1] = answer
        random.shuffle(choices)
        return {"a": cost, "b": sell, "c": None, "d": None, "operation": operation,
                "answer": answer, "choices": choices}

    if operation == "percent_successive":
        n = _rand_round_base(level)
        p1 = _rand_percent() * random.choice([1, -1])
        p2 = _rand_percent() * random.choice([1, -1])
        step1 = round(n * (100 + p1) / 100)
        step2 = round(step1 * (100 + p2) / 100)
        answer = step2
        choices = [str(v) for v in _make_int_distractors(answer, 3)] + [str(answer)]
        random.shuffle(choices)
        return {"a": n, "b": p1, "c": p2, "d": None, "operation": operation,
                "answer": str(answer), "choices": choices}

    raise ValueError(f"Noma'lum foiz amali: {operation}")


# ============================================================
# ALGEBRA
# ============================================================

_SUPERSCRIPT_DIGITS = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
    "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
}


def _superscript(n: int) -> str:
    return "".join(_SUPERSCRIPT_DIGITS[d] for d in str(n))


def _format_linear(coef: int, const: int, var: str = "x") -> str:
    """Chiziqli ifodani kanonik ko'rinishda formatlaydi: masalan
    (3, -5) -> '3x - 5', (1, 2) -> 'x + 2', (-1, 0) -> '-x', (0, 7) -> '7'."""
    if coef == 0:
        return str(const)
    if coef == 1:
        term = var
    elif coef == -1:
        term = f"-{var}"
    else:
        term = f"{coef}{var}"
    if const == 0:
        return term
    if const > 0:
        return f"{term} + {const}"
    return f"{term} - {abs(const)}"


def _format_terms(terms: list) -> str:
    """[(qiymat, x_hadmi?)] ro'yxatini 'a x + b - c x + d' shaklida
    formatlaydi (birinchi had belgisiz/manfiy bo'lsa '-', keyingilari
    '+ '/'- ' bilan)."""
    parts = []
    for i, (val, is_var) in enumerate(terms):
        mag = abs(val)
        body = ("x" if mag == 1 else f"{mag}x") if is_var else str(mag)
        if i == 0:
            parts.append(f"-{body}" if val < 0 else body)
        else:
            parts.append(("- " if val < 0 else "+ ") + body)
    return " ".join(parts)


def _general_int_distractors(correct: int, count: int = 3, spread: int = None) -> list[int]:
    """Manfiy bo'lishi mumkin bo'lgan butun sonlar uchun distraktorlar
    (arifmetikadagi _make_int_distractors'dan farqli, natijani 0 bilan
    cheklamaydi)."""
    if spread is None:
        spread = max(3, abs(correct) // 4 + 4)
    distractors: set = set()
    attempts = 0
    while len(distractors) < count and attempts < 200:
        attempts += 1
        delta = random.randint(-spread, spread)
        if delta == 0:
            continue
        candidate = correct + delta
        if candidate == correct or candidate in distractors:
            continue
        distractors.add(candidate)
    filler = 1
    while len(distractors) < count:
        for cand in (correct + filler, correct - filler):
            if cand != correct and cand not in distractors:
                distractors.add(cand)
            if len(distractors) >= count:
                break
        filler += 1
    return list(distractors)[:count]


def _linear_distractors(coef: int, const: int, count: int = 3) -> list[str]:
    correct_str = _format_linear(coef, const)
    seen = {correct_str}
    out: list[str] = []
    candidates = []
    for delta in (-2, -1, 1, 2):
        candidates.append((coef + delta, const))
        candidates.append((coef, const + delta))
    for dc in (-1, 1):
        for dk in (-1, 1):
            candidates.append((coef + dc, const + dk))
    random.shuffle(candidates)
    for co, cn in candidates:
        if len(out) >= count:
            break
        s = _format_linear(co, cn)
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    filler = 1
    while len(out) < count:
        s = _format_linear(coef, const + filler)
        if s not in seen:
            seen.add(s)
            out.append(s)
        filler += 1
    return out[:count]


_ALGEBRA_RANGE = {1: 8, 2: 10, 3: 14, 4: 18, 5: 25}


def _algebra_equation(level: int) -> dict:
    rng = _ALGEBRA_RANGE.get(level, 12)
    if level == 1:
        x = random.randint(-rng, rng)
        b = random.randint(1, rng)
        c = x + b
        display_text = f"{_format_linear(1, b)} = {c}"
    elif level == 2:
        a = random.randint(2, 9)
        x = random.choice([v for v in range(-rng, rng + 1) if v != 0])
        c = a * x
        display_text = f"{_format_linear(a, 0)} = {c}"
    elif level == 3:
        a = random.randint(2, 9)
        x = random.randint(-rng, rng)
        b = random.randint(1, rng)
        c = a * x + b
        display_text = f"{_format_linear(a, b)} = {c}"
    elif level == 4:
        a = random.randint(2, 9)
        b = random.choice([v for v in range(-9, 10) if v != 0])
        d = random.choice([v for v in range(-20, 21) if v != 0])
        x = random.randint(-rng, rng)
        c = a * (x + b) + d
        d_part = f"+ {d}" if d > 0 else f"- {abs(d)}"
        display_text = f"{a}({_format_linear(1, b)}) {d_part} = {c}"
    else:
        a = m = n = e = f = 2
        for _ in range(50):
            a = random.randint(2, 5)
            m = random.randint(2, 4)
            n = random.choice([v for v in range(-9, 10) if v != 0])
            e = random.randint(2, 6)
            f = random.choice([v for v in range(-9, 10) if v != 0])
            if a * m - e != 0:
                break
        x = random.randint(-rng, rng)
        c = a * (m * x + n) - e * (x + f)
        display_text = f"{a}({_format_linear(m, n)}) - {e}({_format_linear(1, f)}) = {c}"

    answer = x
    choices = [str(v) for v in _general_int_distractors(answer, 3)] + [str(answer)]
    random.shuffle(choices)
    return {
        "a": None, "b": None, "c": None, "d": None,
        "operation": "algebra_equation", "answer": str(answer), "choices": choices,
        "display_text": display_text,
    }


_INEQ_OPS = [(">", "<"), ("<", ">"), ("≥", "≤"), ("≤", "≥")]


def _algebra_inequality(level: int) -> dict:
    rng = _ALGEBRA_RANGE.get(level, 12)
    a = random.randint(1, min(9, 2 + level))
    b = random.randint(-rng, rng)
    k = random.randint(-rng, rng)
    op, flipped = random.choice(_INEQ_OPS)
    c = a * k + b
    display_text = f"{_format_linear(a, b)} {op} {c}"
    answer = f"x {op} {k}"

    seen = {answer}
    choices = [answer]
    for dk in _general_int_distractors(k, 2):
        s = f"x {op} {dk}"
        if s not in seen:
            seen.add(s)
            choices.append(s)
    flip_variant = f"x {flipped} {k}"
    if flip_variant not in seen:
        seen.add(flip_variant)
        choices.append(flip_variant)
    filler = 3
    while len(choices) < 4:
        s = f"x {op} {k + filler}"
        if s not in seen:
            seen.add(s)
            choices.append(s)
        filler += 1
    choices = choices[:4]
    random.shuffle(choices)
    return {
        "a": None, "b": None, "c": None, "d": None,
        "operation": "algebra_inequality", "answer": answer, "choices": choices,
        "display_text": display_text,
    }


def _algebra_expand(level: int) -> dict:
    a = random.randint(2, 4 + level)
    b = random.choice([v for v in range(-6 - level, 7 + level) if v != 0])
    c = random.choice([v for v in range(-9 - level, 10 + level) if v != 0])
    inner = _format_linear(b, c)
    display_text = f"{a}({inner})"
    coef, const = a * b, a * c
    answer = _format_linear(coef, const)
    choices = _linear_distractors(coef, const, 3) + [answer]
    random.shuffle(choices)
    return {
        "a": None, "b": None, "c": None, "d": None,
        "operation": "algebra_expand", "answer": answer, "choices": choices,
        "display_text": display_text,
    }


def _algebra_simplify(level: int) -> dict:
    rng = 5 + level * 2
    coef1 = random.choice([v for v in range(-rng, rng + 1) if v != 0])
    coef2 = random.choice([v for v in range(-rng, rng + 1) if v != 0])
    const1 = random.choice([v for v in range(-rng * 2, rng * 2 + 1) if v != 0])
    const2 = random.choice([v for v in range(-rng * 2, rng * 2 + 1) if v != 0])
    terms = [(coef1, True), (coef2, True), (const1, False), (const2, False)]
    random.shuffle(terms)
    display_text = _format_terms(terms)
    sum_coef, sum_const = coef1 + coef2, const1 + const2
    answer = _format_linear(sum_coef, sum_const)
    choices = _linear_distractors(sum_coef, sum_const, 3) + [answer]
    random.shuffle(choices)
    return {
        "a": None, "b": None, "c": None, "d": None,
        "operation": "algebra_simplify", "answer": answer, "choices": choices,
        "display_text": display_text,
    }


_EXP_BASE_RANGE = {1: (2, 6), 2: (2, 8), 3: (2, 10), 4: (2, 12), 5: (2, 15)}
_EXP_POWER_RANGE = {1: (2, 2), 2: (2, 2), 3: (2, 3), 4: (2, 3), 5: (2, 4)}


def _algebra_exponent(level: int) -> dict:
    base_lo, base_hi = _EXP_BASE_RANGE.get(level, (2, 10))
    pow_lo, pow_hi = _EXP_POWER_RANGE.get(level, (2, 3))
    base = random.randint(base_lo, base_hi)
    exp = random.randint(pow_lo, pow_hi)
    answer = base ** exp
    choices = [str(v) for v in _make_int_distractors(answer, 3)] + [str(answer)]
    random.shuffle(choices)
    return {
        "a": base, "b": exp, "c": None, "d": None,
        "operation": "algebra_exponent", "answer": str(answer), "choices": choices,
    }


_ROOT_SQUARE_RANGE = {1: (2, 8), 2: (2, 12), 3: (2, 16), 4: (2, 20), 5: (2, 25)}
_ROOT_CUBE_RANGE = {1: (2, 4), 2: (2, 5), 3: (2, 6), 4: (2, 8), 5: (2, 10)}


def _algebra_root(level: int) -> dict:
    use_cube = level >= 3 and random.random() < 0.4
    if use_cube:
        lo, hi = _ROOT_CUBE_RANGE.get(level, (2, 6))
        root = random.randint(lo, hi)
        radicand, degree = root ** 3, 3
    else:
        lo, hi = _ROOT_SQUARE_RANGE.get(level, (2, 15))
        root = random.randint(lo, hi)
        radicand, degree = root ** 2, 2
    answer = root
    choices = [str(v) for v in _make_int_distractors(answer, 3)] + [str(answer)]
    random.shuffle(choices)
    return {
        "a": radicand, "b": degree, "c": None, "d": None,
        "operation": "algebra_root", "answer": str(answer), "choices": choices,
    }


def _algebra_system(level: int) -> dict:
    rng = _ALGEBRA_RANGE.get(level, 12)
    x = random.randint(-rng, rng)
    y = random.randint(-rng, rng)
    s, d = x + y, x - y
    display_text = f"x + y = {s}\nx - y = {d}"
    answer = x
    choices = [str(v) for v in _general_int_distractors(answer, 3)] + [str(answer)]
    random.shuffle(choices)
    return {
        "a": None, "b": None, "c": None, "d": None,
        "operation": "algebra_system", "answer": str(answer), "choices": choices,
        "display_text": display_text,
    }


def _generate_algebra_question(operation: str, level: int) -> dict:
    if operation == "algebra_equation":
        return _algebra_equation(level)
    if operation == "algebra_inequality":
        return _algebra_inequality(level)
    if operation == "algebra_expand":
        return _algebra_expand(level)
    if operation == "algebra_simplify":
        return _algebra_simplify(level)
    if operation == "algebra_exponent":
        return _algebra_exponent(level)
    if operation == "algebra_root":
        return _algebra_root(level)
    if operation == "algebra_system":
        return _algebra_system(level)
    raise ValueError(f"Noma'lum algebra amali: {operation}")


# ============================================================
# GEOMETRIYA
# ============================================================

_GEO_RANGE = {1: 10, 2: 15, 3: 20, 4: 30, 5: 50}
_PI = 3.14


def _geo_perimeter(level: int) -> dict:
    rng = _GEO_RANGE.get(level, 20)
    a = random.randint(2, rng)
    b = random.randint(2, rng)
    answer = 2 * (a + b)
    choices = [str(v) for v in _make_int_distractors(answer, 3)] + [str(answer)]
    random.shuffle(choices)
    return {"a": a, "b": b, "c": None, "d": None, "operation": "geo_perimeter",
            "answer": str(answer), "choices": choices}


def _geo_area(level: int) -> dict:
    rng = _GEO_RANGE.get(level, 20)
    a = random.randint(2, rng)
    b = random.randint(2, rng)
    answer = a * b
    choices = [str(v) for v in _make_int_distractors(answer, 3)] + [str(answer)]
    random.shuffle(choices)
    return {"a": a, "b": b, "c": None, "d": None, "operation": "geo_area",
            "answer": str(answer), "choices": choices}


def _geo_volume(level: int) -> dict:
    rng = max(3, _GEO_RANGE.get(level, 20) // 2)
    a = random.randint(2, rng)
    b = random.randint(2, rng)
    c = random.randint(2, rng)
    answer = a * b * c
    choices = [str(v) for v in _make_int_distractors(answer, 3)] + [str(answer)]
    random.shuffle(choices)
    return {"a": a, "b": b, "c": c, "d": None, "operation": "geo_volume",
            "answer": str(answer), "choices": choices}


def _geo_triangle(level: int) -> dict:
    rng = _GEO_RANGE.get(level, 20)
    while True:
        a = random.randint(2, rng)
        b = random.randint(2, rng)
        if (a * b) % 2 == 0:
            break
    answer = a * b // 2
    choices = [str(v) for v in _make_int_distractors(answer, 3)] + [str(answer)]
    random.shuffle(choices)
    return {"a": a, "b": b, "c": None, "d": None, "operation": "geo_triangle",
            "answer": str(answer), "choices": choices}


def _geo_quad(level: int) -> dict:
    rng = _GEO_RANGE.get(level, 20)
    while True:
        a = random.randint(2, rng)
        b = random.randint(2, rng)
        if (a + b) % 2 == 0:
            break
    c = random.randint(2, rng)
    answer = (a + b) // 2 * c
    choices = [str(v) for v in _make_int_distractors(answer, 3)] + [str(answer)]
    random.shuffle(choices)
    return {"a": a, "b": b, "c": c, "d": None, "operation": "geo_quad",
            "answer": str(answer), "choices": choices}


def _fmt_pi_result(value: float) -> str:
    rounded = round(value, 2)
    if rounded == int(rounded):
        return str(int(rounded))
    s = f"{rounded:.2f}".rstrip("0").rstrip(".")
    return s


def _pi_distractors(correct: float, count: int = 3) -> list[str]:
    correct_str = _fmt_pi_result(correct)
    seen = {correct_str}
    out: list[str] = []
    deltas = [0.5, -0.5, 1, -1, 2, -2, 0.25, -0.25]
    random.shuffle(deltas)
    for delta in deltas:
        if len(out) >= count:
            break
        val = correct + delta
        if val <= 0:
            continue
        s = _fmt_pi_result(val)
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
    filler = 3
    while len(out) < count:
        val = correct + filler
        s = _fmt_pi_result(val)
        if s not in seen:
            seen.add(s)
            out.append(s)
        filler += 1
    return out[:count]


def _geo_circle(level: int) -> dict:
    rng = _GEO_RANGE.get(level, 20)
    radius = random.randint(2, max(3, rng // 2))
    kind = random.choice([1, 2])  # 1 = uzunlik (aylana), 2 = yuza
    value = 2 * _PI * radius if kind == 1 else _PI * radius * radius
    answer = _fmt_pi_result(value)
    choices = _pi_distractors(value, 3) + [answer]
    random.shuffle(choices)
    return {"a": radius, "b": None, "c": kind, "d": None, "operation": "geo_circle",
            "answer": answer, "choices": choices}


_PYTH_TRIPLES = [
    (3, 4, 5), (6, 8, 10), (5, 12, 13), (8, 15, 17),
    (7, 24, 25), (9, 12, 15), (20, 21, 29),
]


def _geo_pythagoras(level: int) -> dict:
    leg1, leg2, hyp = random.choice(_PYTH_TRIPLES)
    max_mult = {1: 1, 2: 2, 3: 3, 4: 4, 5: 5}.get(level, 2)
    mult = random.randint(1, max_mult)
    a, b, answer = leg1 * mult, leg2 * mult, hyp * mult
    choices = [str(v) for v in _make_int_distractors(answer, 3)] + [str(answer)]
    random.shuffle(choices)
    return {"a": a, "b": b, "c": None, "d": None, "operation": "geo_pythagoras",
            "answer": str(answer), "choices": choices}


def _geo_angles(level: int) -> dict:
    while True:
        a = random.randint(10, 20 + level * 15)
        b = random.randint(10, 20 + level * 15)
        if a + b < 175:
            break
    answer = 180 - a - b
    distractor_vals = _make_int_distractors(answer, 3)
    answer_str = f"{answer}°"
    choices = [f"{v}°" for v in distractor_vals] + [answer_str]
    random.shuffle(choices)
    return {"a": a, "b": b, "c": None, "d": None, "operation": "geo_angles",
            "answer": answer_str, "choices": choices}


def _generate_geometry_question(operation: str, level: int) -> dict:
    if operation == "geo_perimeter":
        return _geo_perimeter(level)
    if operation == "geo_area":
        return _geo_area(level)
    if operation == "geo_volume":
        return _geo_volume(level)
    if operation == "geo_triangle":
        return _geo_triangle(level)
    if operation == "geo_quad":
        return _geo_quad(level)
    if operation == "geo_circle":
        return _geo_circle(level)
    if operation == "geo_pythagoras":
        return _geo_pythagoras(level)
    if operation == "geo_angles":
        return _geo_angles(level)
    raise ValueError(f"Noma'lum geometriya amali: {operation}")


# ============================================================
# FUNKSIYALAR
# ============================================================

_FUNC_COEF_RANGE = {1: 5, 2: 7, 3: 9, 4: 11, 5: 14}
_FUNC_CONST_RANGE = {1: 10, 2: 15, 3: 20, 4: 25, 5: 30}
_FUNC_X_RANGE = {1: 6, 2: 8, 3: 10, 4: 12, 5: 15}


def _rand_nonzero(lo_abs: int, hi_abs: int) -> int:
    v = random.randint(lo_abs, hi_abs)
    return v if random.random() < 0.5 else -v


def _func_linear(level: int) -> dict:
    coef_max = _FUNC_COEF_RANGE.get(level, 9)
    const_max = _FUNC_CONST_RANGE.get(level, 20)
    x_max = _FUNC_X_RANGE.get(level, 10)
    k = _rand_nonzero(1, coef_max)
    b = random.randint(-const_max, const_max)
    x = random.randint(-x_max, x_max)
    y = k * x + b
    choices = [str(v) for v in _general_int_distractors(y, 3)] + [str(y)]
    random.shuffle(choices)
    return {"a": k, "b": b, "c": x, "d": None, "operation": "func_linear",
            "answer": str(y), "choices": choices}


def _func_quadratic(level: int) -> dict:
    coef_max = max(2, _FUNC_COEF_RANGE.get(level, 9) // 2)
    const_max = _FUNC_CONST_RANGE.get(level, 20)
    x_max = min(8, _FUNC_X_RANGE.get(level, 10))
    a = _rand_nonzero(1, coef_max)
    b = random.randint(-const_max, const_max)
    c = random.randint(-const_max, const_max)
    x = random.randint(-x_max, x_max)
    y = a * x * x + b * x + c
    choices = [str(v) for v in _general_int_distractors(y, 3)] + [str(y)]
    random.shuffle(choices)
    return {"a": a, "b": b, "c": c, "d": x, "operation": "func_quadratic",
            "answer": str(y), "choices": choices}


def _func_graph(level: int) -> dict:
    coef_max = _FUNC_COEF_RANGE.get(level, 9)
    const_max = _FUNC_CONST_RANGE.get(level, 20)
    k = _rand_nonzero(1, coef_max)
    b = random.randint(-const_max, const_max)
    answer = b
    choices = [str(v) for v in _general_int_distractors(answer, 3)] + [str(answer)]
    random.shuffle(choices)
    return {"a": k, "b": b, "c": None, "d": None, "operation": "func_graph",
            "answer": str(answer), "choices": choices}


def _func_value(level: int) -> dict:
    q = _func_linear(level) if random.random() < 0.5 else _func_quadratic(level)
    q["operation"] = "func_value"
    return q


def _func_zeros(level: int) -> dict:
    coef_max = _FUNC_COEF_RANGE.get(level, 9)
    x_max = _FUNC_X_RANGE.get(level, 10)
    k = _rand_nonzero(1, coef_max)
    x = random.randint(-x_max, x_max)
    b = -k * x
    answer = x
    choices = [str(v) for v in _general_int_distractors(answer, 3)] + [str(answer)]
    random.shuffle(choices)
    return {"a": k, "b": b, "c": None, "d": None, "operation": "func_zeros",
            "answer": str(answer), "choices": choices}


def _generate_function_question(operation: str, level: int) -> dict:
    if operation == "func_linear":
        return _func_linear(level)
    if operation == "func_quadratic":
        return _func_quadratic(level)
    if operation == "func_graph":
        return _func_graph(level)
    if operation == "func_value":
        return _func_value(level)
    if operation == "func_zeros":
        return _func_zeros(level)
    raise ValueError(f"Noma'lum funksiya amali: {operation}")


# ============================================================
# EHTIMOLLIK VA STATISTIKA
# ============================================================

_STAT_N = {1: 4, 2: 4, 3: 5, 4: 5, 5: 6}
_STAT_RANGE = {1: 20, 2: 30, 3: 40, 4: 60, 5: 100}


def _stat_mean(level: int) -> dict:
    n = _STAT_N.get(level, 5)
    rng = _STAT_RANGE.get(level, 40)
    mean = random.randint(1, rng)
    total_target = mean * n
    values = [mean] * n
    for _ in range(50):
        candidate = [random.randint(1, rng) for _ in range(n - 1)]
        last = total_target - sum(candidate)
        if 1 <= last <= rng * 3:
            values = candidate + [last]
            break
    random.shuffle(values)
    answer = mean
    choices = [str(v) for v in _make_int_distractors(answer, 3)] + [str(answer)]
    random.shuffle(choices)
    return {"a": None, "b": None, "c": None, "d": None, "operation": "stat_mean",
            "answer": str(answer), "choices": choices, "extra": values}


def _stat_median(level: int) -> dict:
    n = _STAT_N.get(level, 5)
    if n % 2 == 0:
        n += 1  # mediana aniq bitta bo'lishi uchun toq son element
    rng = _STAT_RANGE.get(level, 40)
    if rng + 1 > n:
        values = sorted(random.sample(range(1, rng + 1), n))
    else:
        values = sorted(random.choices(range(1, rng + 1), k=n))
    median = values[n // 2]
    shuffled = values[:]
    random.shuffle(shuffled)
    answer = median
    choices = [str(v) for v in _make_int_distractors(answer, 3)] + [str(answer)]
    random.shuffle(choices)
    return {"a": None, "b": None, "c": None, "d": None, "operation": "stat_median",
            "answer": str(answer), "choices": choices, "extra": shuffled}


def _stat_mode(level: int) -> dict:
    rng = max(6, _STAT_RANGE.get(level, 40) // 4)
    mode_val = random.randint(1, rng)
    n_extra = random.randint(4, 5 + level)
    values = [mode_val, mode_val, mode_val]
    others: set = set()
    attempts = 0
    while len(others) < n_extra and attempts < 100:
        attempts += 1
        v = random.randint(1, rng)
        if v != mode_val:
            others.add(v)
    for v in others:
        times = random.choice([1, 1, 2])
        values.extend([v] * times)
    random.shuffle(values)
    answer = mode_val
    choices = [str(v) for v in _make_int_distractors(answer, 3)] + [str(answer)]
    random.shuffle(choices)
    return {"a": None, "b": None, "c": None, "d": None, "operation": "stat_mode",
            "answer": str(answer), "choices": choices, "extra": values}


def _stat_probability(level: int) -> dict:
    total = random.randint(5, 10 + level * 4)
    favorable = random.randint(1, total - 1)
    g = math.gcd(favorable, total)
    num, den = favorable // g, total // g
    answer = f"{num}/{den}"
    choices = _frac_basic_distractors(num, den, 3) + [answer]
    random.shuffle(choices)
    return {"a": favorable, "b": total, "c": None, "d": None, "operation": "stat_probability",
            "answer": answer, "choices": choices}


_COMBINATORICS_N = {1: (3, 4), 2: (3, 5), 3: (4, 6), 4: (4, 7), 5: (5, 8)}


def _stat_combinatorics(level: int) -> dict:
    lo, hi = _COMBINATORICS_N.get(level, (3, 6))
    n = random.randint(lo, hi)
    answer = math.factorial(n)
    choices = [str(v) for v in _general_int_distractors(answer, 3, spread=max(6, answer // 3))] + [str(answer)]
    random.shuffle(choices)
    return {"a": n, "b": None, "c": None, "d": None, "operation": "stat_combinatorics",
            "answer": str(answer), "choices": choices}


def _generate_statistics_question(operation: str, level: int) -> dict:
    if operation == "stat_mean":
        return _stat_mean(level)
    if operation == "stat_median":
        return _stat_median(level)
    if operation == "stat_mode":
        return _stat_mode(level)
    if operation == "stat_probability":
        return _stat_probability(level)
    if operation == "stat_combinatorics":
        return _stat_combinatorics(level)
    raise ValueError(f"Noma'lum statistika amali: {operation}")


# ============================================================
# UMUMIY DISPATCH
# ============================================================

_SPECIAL_ARITHMETIC_OPS = {"arith_order", "arith_remainder", "arith_negative"}
_SPECIAL_ARITHMETIC_FUNCS = {
    "arith_order": _arith_order,
    "arith_remainder": _arith_remainder,
    "arith_negative": _arith_negative,
}


def generate_question(operation: str, digits: int) -> dict:
    if operation in FRACTION_OPS:
        return _generate_fraction_question(operation, digits)
    if operation in PERCENT_OPS:
        return _generate_percent_question(operation, digits)
    if operation in ALGEBRA_OPS:
        return _generate_algebra_question(operation, digits)
    if operation in GEOMETRY_OPS:
        return _generate_geometry_question(operation, digits)
    if operation in FUNCTION_OPS:
        return _generate_function_question(operation, digits)
    if operation in STATISTICS_OPS:
        return _generate_statistics_question(operation, digits)
    if operation in _SPECIAL_ARITHMETIC_OPS:
        return _SPECIAL_ARITHMETIC_FUNCS[operation](digits)
    if operation in ARITHMETIC_OPS:
        return _generate_arithmetic_question(operation, digits)
    raise ValueError(f"Noma'lum amal: {operation}")


def generate_test(operation: str, digits: int, count: int) -> list[dict]:
    """Bitta test uchun `count` ta noyob misol generatsiya qiladi."""
    questions = []
    seen = set()
    attempts = 0
    while len(questions) < count and attempts < count * 30:
        attempts += 1
        q = generate_question(operation, digits)
        extra = q.get("extra")
        key = (q["a"], q["b"], q["c"], q["d"], q.get("display_text"),
               tuple(extra) if extra is not None else None)
        if key in seen:
            continue
        seen.add(key)
        questions.append(q)
    # agar noyob kombinatsiyalar yetmasa, takrorlansa ham to'ldiramiz
    while len(questions) < count:
        questions.append(generate_question(operation, digits))
    return questions
