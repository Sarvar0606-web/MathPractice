"""Arifmetik misollarni (savollarni) generatsiya qilish."""
import random


def _rand_n_digit(digits: int) -> int:
    """digits xonali tasodifiy musbat son qaytaradi (masalan 2 xonali: 10-99)."""
    if digits <= 0:
        return 0
    low = 10 ** (digits - 1) if digits > 1 else 0
    high = 10 ** digits - 1
    return random.randint(low, high)


def _generate_pair(operation: str, digits: int) -> tuple[int, int, int]:
    """operation va digits asosida (a, b, javob) qaytaradi."""
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

    raise ValueError(f"Noma'lum amal: {operation}")


def _make_distractors(correct: int, count: int = 3) -> list[int]:
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


def generate_question(operation: str, digits: int) -> dict:
    a, b, answer = _generate_pair(operation, digits)
    choices = _make_distractors(answer, 3) + [answer]
    random.shuffle(choices)
    return {
        "a": a,
        "b": b,
        "operation": operation,
        "answer": answer,
        "choices": choices,
    }


def generate_test(operation: str, digits: int, count: int) -> list[dict]:
    """Bitta test uchun `count` ta noyob misol generatsiya qiladi."""
    questions = []
    seen = set()
    attempts = 0
    while len(questions) < count and attempts < count * 20:
        attempts += 1
        q = generate_question(operation, digits)
        key = (q["a"], q["b"])
        if key in seen:
            continue
        seen.add(key)
        questions.append(q)
    # agar noyob kombinatsiyalar yetmasa, takrorlansa ham to'ldiramiz
    while len(questions) < count:
        questions.append(generate_question(operation, digits))
    return questions
