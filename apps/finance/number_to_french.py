"""Convert a number to French words for Moroccan invoice compliance."""

ONES = [
    "", "un", "deux", "trois", "quatre", "cinq", "six", "sept",
    "huit", "neuf", "dix", "onze", "douze", "treize", "quatorze",
    "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf",
]
TENS = [
    "", "", "vingt", "trente", "quarante", "cinquante",
    "soixante", "soixante-dix", "quatre-vingts", "quatre-vingt-dix",
]


def _below_thousand(n):
    if n == 0:
        return ""
    if n < 20:
        return ONES[n]
    if n < 100:
        t, o = divmod(n, 10)
        s = TENS[t]
        if t == 7 or t == 9:
            if o == 1:
                s += "-et-" + ONES[1]
            elif o:
                s += "-" + ONES[o + 10]
        elif o:
            s += "-" + ONES[o] if (t != 8 or o != 0) else "-et-" if o == 1 else "-" + ONES[o]
        return s
    h, rest = divmod(n, 100)
    prefix = ""
    if h == 1:
        prefix = "cent"
    else:
        prefix = ONES[h] + "-cent"
    if rest == 0 and h > 1:
        return prefix + "s"
    return (prefix + " " + _below_thousand(rest)).strip()


def _group_words(n, group_name, feminine=False):
    if n == 0:
        return ""
    words = _below_thousand(n)
    if n == 1:
        word = "un" if not feminine else "une"
    else:
        word = words
    if group_name:
        word += " " + group_name
        if n > 1:
            word += "s"
    return word


def number_to_french(amount):
    """Convert a Decimal amount to French words, e.g. 'Dix mille deux cent cinquante-dirhams et 00 centimes'"""
    from decimal import Decimal

    amount = Decimal(str(amount))
    dirhams = int(amount)
    centimes = int(round((amount - dirhams) * 100))

    if dirhams == 0 and centimes == 0:
        return "zéro-dirham et zéro centime"

    parts = []
    thousands, remainder = divmod(dirhams, 1000)
    millions, thousands = divmod(thousands, 1000)
    milliards, millions = divmod(millions, 1000)

    if milliards:
        parts.append(_group_words(milliards, "milliard"))
    if millions:
        if millions == 1:
            parts.append("un million")
        else:
            parts.append(_below_thousand(millions) + " millions")
    if thousands:
        if thousands == 1:
            parts.append("mille")
        else:
            parts.append(_below_thousand(thousands) + " mille")
    if remainder:
        parts.append(_below_thousand(remainder))

    word = " ".join(parts).strip()
    if not word:
        word = "zéro"
    word += "-dirham" if dirhams != 1 else "-dirham"

    if centimes:
        cents = _below_thousand(centimes)
        word += " et " + cents + (" centime" if centimes == 1 else " centimes")
    else:
        word += " et zéro centime"

    return word
