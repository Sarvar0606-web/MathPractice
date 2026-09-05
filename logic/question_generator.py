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

ARITHMETIC_OPS = {"add", "sub", "mul", "div", "compare"}
FRACTION_OPS = {
    "frac_compare", "frac_simplify", "frac_add", "frac_sub",
    "frac_mul", "frac_div", "frac_mixed", "frac_decimal",
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

    raise ValueError(f"Noma'lum kasr amali: {operation}")


# ============================================================
# UMUMIY DISPATCH
# ============================================================

def generate_question(operation: str, digits: int) -> dict:
    if operation in FRACTION_OPS:
        return _generate_fraction_question(operation, digits)
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
        key = (q["a"], q["b"], q["c"], q["d"])
        if key in seen:
            continue
        seen.add(key)
        questions.append(q)
    # agar noyob kombinatsiyalar yetmasa, takrorlansa ham to'ldiramiz
    while len(questions) < count:
        questions.append(generate_question(operation, digits))
    return questions
